# DevOps Challenge — FastAPI on AWS

A production-ready FastAPI application deployed to AWS EC2 via Docker, provisioned entirely with Terraform, and automated end-to-end with GitHub Actions.

---

## Architecture Overview

```
┌─────────────┐   push to main   ┌──────────────────────────────────────┐
│   Developer │ ──────────────►  │         GitHub Actions                │
└─────────────┘                  │  build-and-test → push-to-ecr → deploy│
                                 └──────────────┬───────────────┬────────┘
                                                │               │
                                         push image          SSH deploy
                                                │               │
                                                ▼               ▼
                                         ┌─────────┐    ┌─────────────┐
                                         │   ECR   │    │  EC2 t3.micro│
                                         │(private │    │  (Docker)    │
                                         │registry)│    │  port 80     │
                                         └─────────┘    └─────────────┘
                                                               │
                                                    IAM instance role
                                                    (pulls from ECR)
```

**AWS resources (all Terraform-managed):**

| Resource | Purpose |
|----------|---------|
| VPC (10.0.0.0/16) | Isolated network |
| Public subnet + IGW | Internet-accessible host |
| Route table | Routes 0.0.0.0/0 → IGW |
| EC2 t3.micro | Runs the Docker container |
| Security group | Allows inbound 22/80/443, all egress |
| IAM role + instance profile | EC2 pulls from ECR without stored credentials |
| ECR repository | Private Docker image registry |
| CloudWatch log group | `/aws/ec2/devops-challenge-prod`, 7-day retention |
| CloudWatch CPU alarm | Fires when CPU > 80% for ≥ 4 minutes |

---

## Project Structure

```
app/
  main.py              FastAPI application
  requirements.txt     Python dependencies
  Dockerfile           Container image definition
  tests/
    test_main.py       Pytest unit tests
terraform/
  main.tf              Root module: provider, modules, ECR, CloudWatch
  variables.tf         All input variables with defaults
  outputs.tf           Key outputs (EC2 IP, ECR URL, VPC ID)
  modules/
    networking/        VPC, subnet, IGW, route table
    ec2/               Instance, IAM role, security group, user_data
.github/
  workflows/
    ci-cd.yml          Build → test → push → deploy pipeline
docker-compose.yml     Local development environment
```

---

## Quick Start — Local Development

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `{"status": "healthy"}` |
| `GET` | `/items` | List all items |
| `POST` | `/items` | Create an item (`name`, `price` required; `description` optional) |
| `GET` | `/items/{id}` | Fetch a single item by UUID |

---

## Deployment Steps

### Prerequisites

- Terraform ≥ 1.5 installed
- AWS CLI configured with credentials that have EC2, VPC, ECR, IAM, and CloudWatch permissions
- An existing EC2 key pair in the target region (Terraform references it by name — it does not create one)

### 1. Provision Infrastructure

```bash
cd terraform
terraform init
terraform plan -var="key_name=<your-key-pair-name>"
terraform apply -var="key_name=<your-key-pair-name>"
```

Note the outputs:

```
ec2_public_ip      = "1.2.3.4"
ecr_repository_url = "123456789.dkr.ecr.us-east-1.amazonaws.com/devops-challenge-prod"
vpc_id             = "vpc-abc123"
```

### 2. Configure GitHub Secrets

Repository → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|--------|-------|
| `AWS_ACCESS_KEY_ID` | IAM user access key with ECR push permissions |
| `AWS_SECRET_ACCESS_KEY` | IAM user secret key |
| `EC2_HOST` | `ec2_public_ip` from Terraform output |
| `EC2_SSH_KEY` | Contents of the `.pem` private key file |

Update `ECR_REPOSITORY` at the top of `.github/workflows/ci-cd.yml` if you changed `app_name` or `environment` variables from their defaults (`devops-challenge-prod`).

### 3. Deploy

Push any commit to `main`. The pipeline runs automatically:

1. **build-and-test** — installs Python deps, runs pytest, builds the Docker image as a smoke test
2. **push-to-ecr** — authenticates to ECR, pushes the image tagged with the Git SHA and `latest`
3. **deploy** — SSHes into EC2, authenticates Docker via the instance role, pulls the new image, restarts the container on port 80

### 4. Verify

```bash
curl http://<EC2_HOST>/health
# {"status":"healthy"}
```

---

## Design Decisions

**Modular Terraform** — networking and EC2 concerns live in separate reusable modules. The root `main.tf` is deliberately thin: it wires the modules together and owns cross-cutting resources (ECR, CloudWatch). This mirrors how real teams share modules across environments.

**ECR image tagged by Git SHA** — every push creates a unique, immutable image tag alongside `latest`. This means rollback is re-running the deploy step with any prior SHA; no new build required.

**IAM instance role for ECR authentication** — the EC2 instance carries an IAM profile with `AmazonEC2ContainerRegistryReadOnly`. The SSH deploy script calls `aws ecr get-login-password` which resolves credentials via the instance metadata service. No AWS keys are ever written to the host.

**Sequential CI jobs gate the pipeline** — `build-and-test` must pass before pushing to ECR; the push must succeed before deploying. A broken image is never shipped; a failed push means no partial deployment.

**Simple in-memory item store** — the `/items` endpoint uses a Python dict. This keeps the application self-contained (no database to provision for the challenge) and makes the tests deterministic. The Limitations section covers the production gap.

**CloudWatch alarm on built-in EC2 metrics** — CPU utilization is emitted by the hypervisor with no agent required on Amazon Linux 2. This gives immediate observability on a new instance with zero additional setup.

**Docker Compose for local dev** — matches the production container runtime closely (same image, same port mapping) while adding a volume mount for live-reload during development.

---

## Assumptions

- The AWS account has permissions for EC2, VPC, ECR, IAM, and CloudWatch.
- An EC2 key pair already exists in the target region. Terraform references it by name and does not create it (key creation is a one-time manual step; private keys must never be stored in state).
- The deployment region is `us-east-1`. Override with `-var="aws_region=<region>"` and update `aws_region.default` in `variables.tf` accordingly.
- GitHub Actions runners have outbound internet access to reach ECR and SSH to the EC2 public IP.
- Port 22 is reachable from GitHub's runner IP ranges (the security group opens it to 0.0.0.0/0).

---

## Limitations

| Area | Current state | Production path |
|------|--------------|-----------------|
| High availability | Single EC2 instance — one point of failure | Auto Scaling Group behind an Application Load Balancer |
| HTTPS | Port 443 open but no TLS termination | ACM certificate on an ALB, or nginx + Certbot on the instance |
| Terraform state | Local `terraform.tfstate` | S3 backend with DynamoDB state locking |
| SSH to production | Deploy job SSHes directly on port 22 | AWS SSM Session Manager (no open port 22 required) |
| Data persistence | Items lost on container restart | Amazon RDS or DynamoDB |
| Security group | Port 22 open to 0.0.0.0/0 | Restrict to a known CIDR or remove in favour of SSM |
| Multi-AZ | Single availability zone | Subnets in ≥ 2 AZs required for production resilience |
| Observability | Basic CPU alarm only | CloudWatch agent + application-level metrics, structured logging |
