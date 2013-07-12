[program:celerybeat]
command=/srv/www/<%= @appname %>/venv/bin/celery beat --app=app --loglevel=info --logfile=celerybeat.log
directory=/srv/www/<%= @appname %>
user=<%= @user %>
group=<%= @user %>
autostart=true
autorestart=true
redirect_stderr=True
