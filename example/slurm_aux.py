"""
Auxiliary functions to deal with SLURM tokens for astra-web.
"""

import inspect
from typing import Awaitable, Callable
from datetime import datetime

_last_token_renewal: datetime | None = None
_get_new_slurm_token: Callable[[], Awaitable[str] | str] | None = None
_update_slurm_token: Callable[[str], Awaitable[None] | None] | None = None
_check_slurm_token: Callable[[], Awaitable[bool | None] | bool | None] | None = None


def register_get_new_slurm_token_hook(hook: Callable[[], Awaitable[str] | str]):
    """
    Register a hook function that will be called to renew the SLURM token when needed.
    The hook function should return the new token as a string.
    """
    global _get_new_slurm_token
    _get_new_slurm_token = hook


def register_update_slurm_token_hook(hook: Callable[[str], Awaitable[None] | None]):
    """
    Register a hook function that will be called with the new SLURM token when it is renewed.
    The hook function should take the new token as a string argument and update it in the relevant places (e.g. slurm config).
    """
    global _update_slurm_token
    _update_slurm_token = hook


def register_check_slurm_token_hook(hook: Callable[[], Awaitable[bool] | bool]):
    """
    Register a hook function that will be called to check if the current SLURM token is valid.
    The hook function should return True if the token is valid, False otherwise.
    If None is returned instead, it will be interpreted as True, to allow for check hooks that only raise exceptions on failure.
    """
    global _check_slurm_token
    _check_slurm_token = hook


async def renew_slurm_token_if_needed(show: bool = True, max_age_hours: int = 1):

    global _last_token_renewal

    # check if renewal is needed
    if _last_token_renewal is not None:
        delta = datetime.now() - _last_token_renewal
        if delta.total_seconds() < 60 * 60 * max_age_hours:
            if show:
                print(
                    f"SLURM token renewed {delta.total_seconds()/(60*60):.1f} hours ago, skipping renewal."
                )
            # token is still fresh, skip renewal
            return

    # request new token
    if _get_new_slurm_token is None:
        raise RuntimeError(
            "No SLURM token renewal hook registered. Please register a hook using 'register_get_new_slurm_token_hook'."
        )
    token = _get_new_slurm_token()
    token = await token if inspect.isawaitable(token) else token
    _last_token_renewal = datetime.now()

    # update stored token
    if _update_slurm_token is None:
        raise RuntimeError(
            "No SLURM token update hook registered. Please register a hook using 'register_update_slurm_token_hook'."
        )
    update_result = _update_slurm_token(token)
    if inspect.isawaitable(update_result):
        await update_result

    # check credentials and overall status
    if not _check_slurm_token:
        raise RuntimeError(
            "No SLURM token check hook registered. Please register a hook using 'register_check_slurm_token_hook'."
        )
    ok = _check_slurm_token()
    try:
        ok = await ok if inspect.isawaitable(ok) else ok
        # interpret None as success, to allow for check hooks that only raise exceptions on failure
        ok = ok or ok is None
        if not ok:
            raise RuntimeError(f"Failed to renew SLURM token.")
    except Exception as e:
        raise RuntimeError(f"Failed to check SLURM token.") from e
