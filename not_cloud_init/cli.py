import logging
import os
import sys

import rich_click as click

from not_cloud_init.generator import create_cloud_init_config
from not_cloud_init.logger import configure_logging
from not_cloud_init.console_output import print_error, print_warning, set_quiet_mode, print_info

LOG = logging.getLogger()

default_output_path = "cloud-config.yaml"

@click.command(context_settings={'show_default': True})
@click.pass_context
@click.option(
    "-i",
    "--interactive",
    is_flag=True,
    help="Enable interactive mode.",
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Enable quiet output. Only critical errors and essential information will be displayed.",
)
@click.option(
    "-o",
    "--output-path",
    default=default_output_path,
    help="Path to output file.",
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Write over output file if it already exists.",
)
@click.option(
    "--enable-hostname",
    is_flag=True,
    default=False,
    help="Enable gathering the hostname of the machine. This will cause issues unless this exact machine is being redeployed using the generated cloud-init config.",
)
@click.option(
    "--gather-public-keys",
    is_flag=True,
    help="Enable gathering of all public key files in the ~/.ssh directory. This will allow you to use the same public keys on the new machine as the current machine.",
    default=False,
)
@click.option(
    "--password",
    help="Set the password for the user. WARNING: This is incredibly insecure and is stored in plaintext in the cloud-init config.",
    required=False,
)
@click.option(
    "--disable-apt",
    is_flag=True,
    help="Disable the gathering and generation of apt config.",
    default=False,
)
@click.option(
    "--disable-snap",
    is_flag=True,
    help="Disable the gathering and generation of snap config.",
    default=False,
)
@click.option(
    "--disable-ssh",
    is_flag=True,
    help="Disable the gathering and generation of ssh config.",
    default=False,
)
@click.option(
    "--disable-user",
    is_flag=True,
    help="Disable the gathering and generation of user config.",
    default=False,
)
@click.option(
    "--rename-to-ubuntu-user",
    is_flag=True,
    help="Keep the current user but rename it to the default 'ubuntu' user.",
    default=False,
)
# add -h as a shortcut for --help
@click.help_option("-h", "--help")
@click.version_option()
def cli(
    ctx,
    interactive,
    quiet,
    output_path,
    force,
    gather_public_keys,
    password,
    disable_apt,
    disable_snap,
    disable_ssh,
    disable_user,
    enable_hostname,
    rename_to_ubuntu_user,
):
    """
    Generate a cloud-init configuration file for the current machine.

    If interactive mode is enabled, the script will prompt for the necessary
    information to generate the cloud-init config file and step through each
    configuration module and show the cloud-config portion generated by that
    module.
    
    Only -f can be used with -i/--interactive
    """

    configure_logging()

    if quiet:
        set_quiet_mode(True)

    # if in interactive mode and any disabling or enabling is passed, error out
    if interactive and (disable_apt or disable_snap or disable_ssh or disable_user or enable_hostname):
        print_error("Cannot use interactive mode with disabling or enabling specific configurations.")
        sys.exit(1) 

    if interactive and not force:
        output_path = get_output_path(output_path)
    elif os.path.exists(f"{output_path}") and not force:
        print_error(f"Output file {output_path} already exists. Use --force or -f to allow writing over existing file")
        sys.exit(1)
    elif force:
        print_warning(f"Output file {output_path} already exists. Will overwrite file.")


    disabled_configs = []
    if disable_apt:
        disabled_configs.append("apt")
    if disable_snap:
        disabled_configs.append("snap")
    if disable_ssh:
        disabled_configs.append("ssh")
    if disable_user:
        disabled_configs.append("user")
    if not enable_hostname:
        disabled_configs.append("hostname")

    create_cloud_init_config(
        output_path,
        interactive=interactive,
        gather_public_keys=gather_public_keys,
        password=password,
        disabled_configs=disabled_configs,
        rename_to_ubuntu_user=rename_to_ubuntu_user,
        quiet=quiet,
    )

# ask for path to save cloud-init config and provide default
# if already exists, ask if user wants to overwrite (default to no)
# if they say no, abort
def get_output_path(output_path: str) -> str:
    """
    Ask the user for the path to save the cloud-init config file.
    """

    # if the default path is not the default, then don't prompt the user
    # to specify the path since they have already done so
    if output_path == default_output_path:
        # ask for path to save cloud-init config and provide default
        output_path = click.prompt(
            "Enter the path to save the cloud-init config file",
            default=default_output_path,
            show_default=True,
        )

    print_info(f"{output_path} has been selected as the output path.")

    # if already exists, ask if user wants to overwrite (default to no)
    if os.path.exists(output_path):
        overwrite = click.confirm(
            f"The file '{output_path}' already exists. Do you want to overwrite it?",
            default=False,
        )
        # if they say no, abort
        if not overwrite:
            print_error("Aborting because the file already exists and the user chose not to overwrite.")
            sys.exit(1)

    return output_path


def main():
    cli(obj={})

if __name__ == "__main__":
    main()
