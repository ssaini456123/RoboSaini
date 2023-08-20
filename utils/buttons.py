import discord
from typing import Optional


class JumpView(discord.ui.View):
    """
    Creates a button on the message that its being added onto.
    The button can be used to redirect users to urls upon clicking them.
    """

    def __init__(
        self,
        *,
        timeout,
        url: Optional[str],
        labelName="Jump to message!",
    ):
        super().__init__(timeout=timeout)
        self.add_item(
            discord.ui.Button(
                url=url, label=labelName, style=discord.ButtonStyle.primary
            )
        )
