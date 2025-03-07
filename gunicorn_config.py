bind = "unix:/var/www/emails/emails.sock"
workers = 3
threads = 2
worker_class = "gthread"
worker_connections = 1000
timeout = 300
keepalive = 2

# Access log - records incoming HTTP requests
accesslog = "/var/log/gunicorn/access.log"

# Error log - records Gunicorn server goings-on
errorlog = "/var/log/gunicorn/error.log"

# Whether to send Django output to the error log 
capture_output = True

# How verbose the Gunicorn error logs should be 
loglevel = "info" 