#!/bin/sh -x

python -c "import app.weblib.db; app.weblib.db.init_db()"
