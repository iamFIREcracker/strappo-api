[program:gunicorn]
command=/srv/www/<%= @appname %>/venv/bin/gunicorn -c /srv/www/<%= @appname %>/gunicorn.conf.py run_wsgi:app
directory=/srv/www/<%= @appname %>
user=<%= @user %>
group=<%= @user %>
autostart=true
autorestart=true
redirect_stderr=True
