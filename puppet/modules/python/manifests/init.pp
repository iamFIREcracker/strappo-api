class python {
  include python::modules
  package { ['python', 'python-pip']:
    ensure => installed,
  }
}
