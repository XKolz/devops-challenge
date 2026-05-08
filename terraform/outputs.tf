output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance — set this as EC2_HOST in GitHub Secrets"
  value       = module.ec2.public_ip
}

output "ecr_repository_url" {
  description = "ECR repository URL — update ECR_REPOSITORY in the CI/CD workflow"
  value       = aws_ecr_repository.app.repository_url
}

output "vpc_id" {
  description = "ID of the provisioned VPC"
  value       = module.networking.vpc_id
}
