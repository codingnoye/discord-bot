import discord
import os
import asyncio
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} 계정으로 로그인되었습니다 (ID: {bot.user.id})')
    print('------')

@bot.command()
async def sync(ctx, scope: str = None):
    """
    슬래시 커맨드를 동기화합니다.
    사용법:
    !sync guild - 현재 길드에 동기화 (즉시)
    !sync       - 전역 동기화 (최대 1시간 소요)
    """
    try:
        if scope == 'guild':
            bot.tree.copy_global_to(guild=ctx.guild)
            synced = await bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"{len(synced)}개의 커맨드가 이 길드에 동기화되었습니다 (즉시).")
        else:
            synced = await bot.tree.sync()
            await ctx.send(f"{len(synced)}개의 커맨드가 전역으로 동기화되었습니다 (시간이 걸릴 수 있습니다).")
    except Exception as e:
        await ctx.send(f"커맨드 동기화 실패: {e}")

async def load_extensions():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with bot:
        await load_extensions()
        if not TOKEN or TOKEN == 'your_token_here':
            print("오류: .env 파일에서 DISCORD_TOKEN을 찾을 수 없거나 유효하지 않습니다.")
            return
        try:
            await bot.start(TOKEN)
        except discord.errors.PrivilegedIntentsRequired:
            print("\n오류: Privileged Intents가 활성화되지 않았습니다!")
            print("Discord Developer Portal -> Bot -> Privileged Gateway Intents 로 이동하여")
            print("'Message Content Intent'를 활성화해주세요. 변경 사항 저장을 잊지 마세요!\n")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
