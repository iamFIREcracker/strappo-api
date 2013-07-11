[program:celery_beat]
command=/srv/www/<%= @appname %>/venv/bin/celery beat --app=app --loglevel=info --logfile=celery_beat.log
directory=/srv/www/<%= @appname %>
user=<%= @user %>
group=<%= @user %>
autostart=true
autorestart=true
redirect_stderr=True
