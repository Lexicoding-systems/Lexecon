environment           = "production"
aws_region            = "us-east-1"
kubernetes_version    = "1.28"
node_instance_types   = ["t3.small"]
desired_node_count    = 3
min_node_count        = 3
max_node_count        = 10
db_instance_class     = "db.t3.small"
db_allocated_storage  = 100
db_max_allocated_storage = 500
postgres_version      = "15.4"

# Override these with your actual VPC/subnet IDs:
# vpc_id            = "vpc-xxxxxxxx"
# subnet_ids        = ["subnet-xxxxxxxx", "subnet-yyyyyyyy"]
# db_subnet_ids     = ["subnet-zzzzzzzz", "subnet-wwwwwwww"]
