class redis {
  package { [ 'redis' ]:
    ensure => 'installed',
  }
  service { 'redis':
    ensure => running,
    require => Package['redis']
  }
}
