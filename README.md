Contains an ansble playbook and role to create and start kvm machines using libvirt.
To communicate with created hosts, you need an additional macvlan host interface from
the same physical netword interface parent.
See https://major.io/2015/10/26/systemd-networkd-and-macvlan-interfaces/ for a guide
on how to create a macvlan.
