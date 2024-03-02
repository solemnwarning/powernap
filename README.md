# Powernap

The Powernap suite provides tools for shutting down or otherwise reducing power usage of idle computers and remotely waking them up again.

The Powernap package was originally developed by Dustin Kirkland for Ubuntu.

My goal with this project is to bring Powernap up to date with modern Linux/Python conventions, add new features and generally improve it. I'm running it in my own environment and welcome anyone to try it, just bear in mind I might break things at this stage until the first major release of this fork.

## powernapd

The `powernapd` daemon monitors the local system for activity (running processes, disk activity, logged in users, etc) and can be configured to shut down the machine when it has been idle for a while, or any number of progressive power saving actions (stopping services, shutting down devices, etc).

NOTE: The man page for this is currently out of date, see the example configuration installed to `/etc/powernap/powernapd.conf` for an up-to-date reference.

Status: Mostly stable - I intend to do more refactoring here, but there _probably_ won't be any further breaking changes.

## powerwake

The `powerwake` tool allows remotely starting up a computer which has been shut down using WoL (Wake-on-LAN or IPMI).

By default `powerwake` will simply send a power on message to the machine and exit, but it can also wait for the machine to finish booting (detected by contacting the `powernapd` daemon on the target) using the `--wait` option.

NOTE: The man page for this is currently out of date, see `powerwake --help` for an up-to-date reference.

Status: Mostly stable - I intend to do more refactoring here and add features, but there _probably_ won't be any further breaking changes.

## powerwaked

The `powerwaked` daemon monitors the local network for ARP lookups and allows waking configured systems via WoL when they are needed in response.

Status: Unstable - I haven't spent much time on this or made any use of it, expect serious breakage.
