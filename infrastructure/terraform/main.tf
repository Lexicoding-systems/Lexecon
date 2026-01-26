terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "lexecon-terraform-state"
    key            = "lexecon/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Lexecon"
      Environment = var.environment
      ManagedBy   = "Terraform"
      CreatedAt   = timestamp()
    }
  }
}

# Kubernetes Cluster
resource "aws_eks_cluster" "lexecon" {
  name            = "lexecon-${var.environment}"
  role_arn        = aws_iam_role.eks_cluster_role.arn
  version         = var.kubernetes_version

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = true
    endpoint_public_access  = true
    public_access_cidrs     = var.allowed_cidr_blocks
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]

  tags = {
    Name = "lexecon-${var.environment}"
  }
}

# EKS Node Group
resource "aws_eks_node_group" "lexecon" {
  cluster_name    = aws_eks_cluster.lexecon.name
  node_group_name = "lexecon-${var.environment}-nodes"
  node_role_arn   = aws_iam_role.eks_node_role.arn
  subnet_ids      = var.subnet_ids
  version         = var.kubernetes_version

  scaling_config {
    desired_size = var.desired_node_count
    max_size     = var.max_node_count
    min_size     = var.min_node_count
  }

  instance_types = var.node_instance_types

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy
  ]

  tags = {
    Name = "lexecon-${var.environment}-nodes"
  }
}

# RDS PostgreSQL Database
resource "aws_db_instance" "lexecon" {
  identifier     = "lexecon-${var.environment}"
  engine         = "postgres"
  engine_version = var.postgres_version
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.database.arn

  db_name  = "lexecon"
  username = var.db_username
  password = random_password.db_password.result

  db_subnet_group_name            = aws_db_subnet_group.lexecon.name
  vpc_security_group_ids          = [aws_security_group.database.id]
  publicly_accessible             = false
  multi_az                         = var.environment == "production" ? true : false
  backup_retention_period          = var.environment == "production" ? 30 : 7
  backup_window                    = "03:00-04:00"
  maintenance_window               = "mon:04:00-mon:05:00"
  deletion_protection              = var.environment == "production" ? true : false
  skip_final_snapshot              = var.environment == "staging" ? true : false
  final_snapshot_identifier        = var.environment == "production" ? "lexecon-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  performance_insights_enabled = true
  performance_insights_retention_period = var.environment == "production" ? 731 : 7

  enable_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name = "lexecon-${var.environment}"
  }

  depends_on = [aws_db_subnet_group.lexecon]
}

# Database Subnet Group
resource "aws_db_subnet_group" "lexecon" {
  name       = "lexecon-${var.environment}"
  subnet_ids = var.db_subnet_ids

  tags = {
    Name = "lexecon-${var.environment}"
  }
}

# Security Group for Database
resource "aws_security_group" "database" {
  name   = "lexecon-database-${var.environment}"
  vpc_id = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
    description     = "PostgreSQL from EKS nodes"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lexecon-database-${var.environment}"
  }
}

# Security Group for EKS Nodes (for database access)
resource "aws_security_group" "eks_nodes" {
  name   = "lexecon-eks-nodes-${var.environment}"
  vpc_id = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lexecon-eks-nodes-${var.environment}"
  }
}

# KMS Key for Database Encryption
resource "aws_kms_key" "database" {
  description             = "KMS key for Lexecon ${var.environment} database encryption"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  enable_key_rotation     = true

  tags = {
    Name = "lexecon-database-${var.environment}"
  }
}

resource "aws_kms_alias" "database" {
  name          = "alias/lexecon-database-${var.environment}"
  target_key_id = aws_kms_key.database.key_id
}

# Random Database Password
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Secrets Manager for Database Password
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "lexecon/${var.environment}/db/password"
  recovery_window_in_days = var.environment == "production" ? 30 : 7
  kms_key_id              = aws_kms_key.database.id

  tags = {
    Name = "lexecon-${var.environment}-db-password"
  }
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# IAM Roles
resource "aws_iam_role" "eks_cluster_role" {
  name = "lexecon-eks-cluster-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "eks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.eks_cluster_role.name
}

resource "aws_iam_role" "eks_node_role" {
  name = "lexecon-eks-node-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "eks_worker_node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.eks_node_role.name
}

resource "aws_iam_role_policy_attachment" "eks_container_registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.eks_node_role.name
}
