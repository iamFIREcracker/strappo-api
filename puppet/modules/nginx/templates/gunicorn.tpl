upstream <%= @appname %> {
    # server unix:/tmp/gunicorn.sock fail_timeout=0;
    # For a TCP configuration:
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80 default;
    server_name _;

    location /static/ {
        alias /srv/www/<%= @appname %>/static/;
        expires 30d;
    }

    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;

        proxy_pass   http://<%= @appname %>;
    }
}
