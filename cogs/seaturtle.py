import discord
from discord.ext import commands
from google import genai
from google.genai import types
import os
import random
import asyncio

class SeaTurtle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.puzzles = []
        self.active_games = {}  # thread_id -> {puzzle_text, answer_text, history, client, chat_session}
        self.load_puzzles()
        self.configure_gemini()

    def load_puzzles(self):
        try:
            with open('data/puzzles.txt', 'r', encoding='utf-8') as f:
                content = f.read()
            
            parts = content.split('[문제]')
            for part in parts:
                if not part.strip():
                    continue
                if '[해답]' in part:
                    question, answer = part.split('[해답]')
                    self.puzzles.append({
                        'question': question.strip(),
                        'answer': answer.strip()
                    })
            print(f"Loaded {len(self.puzzles)} puzzles.")
        except Exception as e:
            print(f"Error loading puzzles: {e}")

    def configure_gemini(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            print("Warning: GEMINI_API_KEY not found in .env")
            self.client = None

    @commands.hybrid_command(name='바거수', aliases=['바다거북', 'soup'], description="바다거북 수프 게임을 시작합니다.")
    async def start_game(self, ctx):
        if not self.puzzles:
            await ctx.send("등록된 문제가 없습니다.")
            return
        
        if not self.client:
            await ctx.send("Gemini API 키가 설정되지 않아 게임을 시작할 수 없습니다.")
            return

        puzzle = random.choice(self.puzzles)
        
        message = await ctx.send(f"🐢 **바다거북 수프 게임을 시작합니다!**\n스레드에서 게임이 진행됩니다.")
        thread = await message.create_thread(name="바다거북 수프 게임", auto_archive_duration=60)
        await thread.send(f"**문제:**\n{puzzle['question']}\n\n이 스레드에서 질문을 해주세요. 제가 '예', '아니오', 또는 약간의 힌트로 대답해 드립니다.")
        
        self.active_games[thread.id] = {
            'question': puzzle['question'],
            'answer': puzzle['answer'],
            'history': []
        }
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id in self.active_games:
            game_state = self.active_games[message.channel.id]
            
            async with message.channel.typing():
                try:
                    user_input = message.content
                    
                    # Construct prompt with history
                    # Since the new SDK is stateless for generate_content unless we manage history manually or use a chat helper if available.
                    # The user example uses generate_content. Let's stick to that and append history to contents.
                    
                    system_prompt = f"""
                    당신은 '바다거북 수프' 게임의 사회자입니다.
                    
                    [문제]
                    {game_state['question']}
                    
                    [정답]
                    {game_state['answer']}
                    
                    사용자의 질문에 '예', '아니오' 위주로 답하세요. 결정적인 힌트는 주지 마세요.
                    사용자가 정답을 맞추면 반드시 답변 시작에 "[정답]"이라고 쓰고 정답 전체를 공개하세요.
                    
                    대화 내역:
                    """
                    
                    full_content = system_prompt
                    for msg in game_state['history']:
                        full_content += f"\n{msg['role']}: {msg['content']}"
                    
                    full_content += f"\nuser: {user_input}\nmodel: "
                    
                    # Update history
                    game_state['history'].append({'role': 'user', 'content': user_input})
                    
                    response = self.client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=full_content
                    )
                    
                    response_text = response.text
                    
                    # Update history with model response
                    game_state['history'].append({'role': 'model', 'content': response_text})
                    
                    await message.reply(response_text)
                    
                    if "[정답]" in response_text:
                        del self.active_games[message.channel.id]
                        
                except Exception as e:
                    await message.reply(f"오류가 발생했습니다: {e}")
                    print(f"Gemini Error: {e}")

async def setup(bot):
    await bot.add_cog(SeaTurtle(bot))
