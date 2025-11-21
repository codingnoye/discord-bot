import discord
from discord.ext import commands
from discord import app_commands

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="hello", description="당신에게 인사를 건넵니다!")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'안녕하세요, {interaction.user.mention}!')

async def setup(bot):
    await bot.add_cog(General(bot))
