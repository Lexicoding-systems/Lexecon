output "eks_cluster_id" {
  description = "EKS cluster ID"
  value       = aws_eks_cluster.lexecon.id
}

output "eks_cluster_arn" {
  description = "EKS cluster ARN"
  value       = aws_eks_cluster.lexecon.arn
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = aws_eks_cluster.lexecon.endpoint
}

output "eks_cluster_certificate_authority" {
  description = "EKS cluster certificate authority"
  value       = aws_eks_cluster.lexecon.certificate_authority[0].data
  sensitive   = true
}

output "eks_node_group_id" {
  description = "EKS node group ID"
  value       = aws_eks_node_group.lexecon.id
}

output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.lexecon.endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.lexecon.db_name
}

output "rds_master_username" {
  description = "RDS master username"
  value       = aws_db_instance.lexecon.username
  sensitive   = true
}

output "db_password_secret_arn" {
  description = "AWS Secrets Manager ARN for database password"
  value       = aws_secretsmanager_secret.db_password.arn
  sensitive   = true
}

output "kms_key_id" {
  description = "KMS key ID for database encryption"
  value       = aws_kms_key.database.id
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.lexecon.name}"
}
