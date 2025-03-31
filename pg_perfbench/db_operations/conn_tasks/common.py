import asyncio


async def run_command(logger, command: str, check: bool = True) -> str:
    """Run shell command asynchronously"""
    if not command.strip():
        raise Exception('Attempting to run an empty command string.')

    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
            limit=262144,
        )
    except Exception as e:
        raise Exception(
            f'Failed to start subprocess for command: {command}\nError:\n{str(e)} .'
        )

    stdout, stderr = await process.communicate()

    # if return code != 0, log error if check is True
    if process.returncode != 0:
        logger.error(
            f"Command '{command}' failed with exit code {process.returncode}."
        )
        logger.error(f"STDERR: {stderr.decode('utf-8', errors='replace')} .")
        if check:
            # If we want to fail on error
            raise Exception(
                f"Command '{command}' - returned non-zero exit code."
            )
    await process.wait()

    return stdout.decode('utf-8')
