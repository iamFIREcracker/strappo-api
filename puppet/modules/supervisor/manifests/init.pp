class supervisor {
  package { 'supervisor':
    ensure => installed,
  }
  service { 'supervisor':
    ensure => running,
  }
}

define supervisor::app( $appname, $user ) {
  file { "/etc/supervisor/conf.d/gunicorn.conf":
    ensure  => present,
    owner   => root,
    group   => root,
    mode    => '644',
    content => template("supervisor/gunicorn.tpl"),
    require => Package[supervisor],
    notify  => Service[supervisor],
  }
}

define supervisor::celery( $appname, $user ) {
  file { "/etc/supervisor/conf.d/celery.conf":
    ensure  => present,
    owner   => root,
    group   => root,
    mode    => '644',
    content => template("supervisor/celery.tpl"),
    require => Package[supervisor],
    notify  => Service[supervisor],
  }
}

