# -*- coding: utf-8 -*-

import os


# TODO(dittrich): Improve this?
def _is_default(a, b):
    """
    Return "Yes" or "No" depending on whether e is the default
    environment or not.
    """
    return "Yes" if a == b else "No"


def get_local_default_file():
    """Returns the path to the local identifier file."""
    # TODO(dittrich): May need to do this differently to support
    # Windows file systems.
    return os.path.join(os.getcwd(), '.python_secrets_environment')


def save_default_environment(environment=None):
    """Save environment identifier to local file for defaulting."""
    env_file = get_local_default_file()
    with open(env_file, 'w') as f_out:
        f_out.write('{0}\n'.format(str(environment)))
    return True


def clear_saved_default_environment():
    """Remove saved default environment file."""
    env_file = os.path.join(
        os.getcwd(),
        '.python_secrets_environment')
    if os.path.exists(env_file):
        os.remove(env_file)
        return True
    else:
        return False


def get_saved_default_environment():
    """Return environment ID value saved in local file or None."""
    env_file = get_local_default_file()
    saved_default = None
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            saved_default = f.read().replace('\n', '')
    return saved_default


def default_environment():
    """
    Return the default environment identifier.

    There are multiple ways for a user to specify the environment
    to use for python_secrets commands. Some of these involve
    explicit settings (e.g., via command line option, a
    saved value in the current working directory, or an
    environment variable) or implicitly from the name of the
    current working directory.
    """

    #  NOTE(dittrich): I know this code has multiple return points
    #  but it is simpler and easier to understand this way.
    #
    # Highest priority is inhereted environment variable.
    environment = os.getenv('D2_ENVIRONMENT', None)
    if environment is not None:
        return environment
    #
    # Next is saved file in current working directory.
    local_default = get_saved_default_environment()
    if local_default not in ['', None]:
        return local_default
    #
    # Lowest priority is the directory path basename.
    return os.path.basename(os.getcwd())


# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
