# /// script
# dependencies = [
#   "numpy",
#   "pygame-ce",
# ]
# ///

import asyncio
import numpy
import pygame

from sandtris.main import amain

_ = (numpy, pygame)


async def main() -> None:
    await amain()


asyncio.run(main())
