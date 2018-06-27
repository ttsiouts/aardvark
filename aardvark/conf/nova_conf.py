from keystoneauth1 import loading as ks_loading
from oslo_config import cfg


SERVICE_TYPE = 'compute'

compute_group = cfg.OptGroup(
    'compute',
    title='Keystone Service Options',
    help="Configuration options for connecting to the keystone API service"
)

def register_opts(conf):

    conf.register_group(compute_group)

    group = getattr(compute_group, 'name', compute_group)

    ks_loading.register_session_conf_options(conf, group)
    ks_loading.register_auth_conf_options(conf, group)

    adapter_opts = get_ksa_adapter_opts(SERVICE_TYPE)
    conf.register_opts(adapter_opts, group=group)

def get_ksa_adapter_opts(default_service_type, deprecated_opts=None):

    opts = ks_loading.get_adapter_conf_options(
        include_deprecated=False, deprecated_opts=deprecated_opts)

    cfg.set_defaults(opts,
                     valid_interfaces=['internal', 'public'],
                     service_type=default_service_type)
    return opts
