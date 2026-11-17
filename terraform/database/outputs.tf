output "instances" {
  description = "Conexión privada y referencia al secreto maestro para operaciones."
  value = {
    for name, db in aws_db_instance.this : name => {
      host              = db.address
      port              = db.port
      master_secret_arn = db.master_user_secret[0].secret_arn
    }
  }
}
