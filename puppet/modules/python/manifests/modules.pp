class python::modules {
  package { [ 'python-dev', ]:
    ensure => 'installed',
  }
  package { [ 'virtualenv', ]:
    ensure => 'installed',
    provider => 'pip',
  }
}
