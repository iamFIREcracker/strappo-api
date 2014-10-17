[program:<%= @appname %>-uwsgi]
command=/srv/www/<%= @appname %>/venv/bin/gunicorn -c /srv/www/<%= @appname %>/uwsgi.ini
directory=/srv/www/<%= @appname %>
user=<%= @user %>
group=<%= @user %>
autostart=true
autorestart=true
redirect_stderr=True
