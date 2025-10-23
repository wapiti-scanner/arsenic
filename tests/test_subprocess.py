import asyncio
import socket
import sys
from asyncio import SelectorEventLoop

import pytest
import pytest_asyncio

from wapiti_arsenic.subprocess import ThreadedSubprocessImpl, AsyncioSubprocessImpl


@pytest_asyncio.fixture(params=[ThreadedSubprocessImpl, AsyncioSubprocessImpl])
async def impl(request):
    if sys.platform == "win32":
        loop = asyncio.get_running_loop()
        if (
            isinstance(loop, SelectorEventLoop)
            and request.param is AsyncioSubprocessImpl
        ):
            raise pytest.skip(
                "Asyncio Subprocess doesn't work on win32 with selector event loop"
            )
    yield request.param()


@pytest.mark.asyncio
async def test_run_process(impl):
    output = await impl.run_process([sys.executable, "-c", 'print("hello")'])
    assert output.strip() == "hello"


@pytest.mark.asyncio
async def test_start_stop_process(impl, unused_tcp_port):
    proc = await impl.start_process(
        [sys.executable, __file__, str(unused_tcp_port)], sys.stdout
    )
    for _ in range(5):
        try:
            reader, writer = await asyncio.open_connection("localhost", unused_tcp_port)
            break
        except:
            await asyncio.sleep(0.5)
    else:
        raise Exception("could not connect")
    msg = await reader.readexactly(5)
    assert msg == b"hello"
    await impl.stop_process(proc)
    with pytest.raises(Exception):
        for _ in range(5):
            await asyncio.open_connection("localhost", unused_tcp_port)
            await asyncio.sleep(0.5)


def main(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", port))
    sock.listen(1)
    while True:
        client, addr = sock.accept()
        client.send(b"hello")
        client.close()


if __name__ == "__main__":
    main(int(sys.argv[1]))
