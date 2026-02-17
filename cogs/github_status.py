"""
Cog para comandos de estado de GitHub
"""
import discord
from discord import app_commands
from discord.ext import commands
import logging
import aiohttp
from typing import Optional
from datetime import datetime, timezone
import os

from utils.embeds import create_info_embed, create_error_embed

logger = logging.getLogger('discord_bot')


class GitHubStatusCog(commands.Cog):
    """Comandos para ver estado de GitHub (PRs y deployments)"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.repo_owner = os.getenv('GITHUB_REPO_OWNER', 'R-afk2550')
        self.repo_name = os.getenv('GITHUB_REPO_NAME', 'discord-bot-gaming')
    
    def _format_datetime(self, dt_str: str) -> str:
        """Formatea una fecha ISO a formato legible"""
        try:
            dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y %H:%M")
        except:
            return dt_str
    
    def _get_status_emoji(self, state: str, merged: bool = False) -> str:
        """Retorna el emoji correspondiente al estado"""
        if merged:
            return "🟣"  # Merged
        elif state == "open":
            return "🟢"  # Open
        elif state == "closed":
            return "🔴"  # Closed
        return "⚪"  # Unknown
    
    def _get_workflow_emoji(self, status: str, conclusion: Optional[str] = None) -> str:
        """Retorna el emoji correspondiente al estado del workflow"""
        if status == "in_progress" or status == "queued":
            return "🔵"  # In progress
        elif status == "completed":
            if conclusion == "success":
                return "✅"  # Success
            elif conclusion == "failure":
                return "❌"  # Failure
            elif conclusion == "cancelled":
                return "⚪"  # Cancelled
            else:
                return "⚠️"  # Other
        return "⚫"  # Unknown
    
    @app_commands.command(
        name="github_prs",
        description="Ver el estado de todos los pull requests abiertos"
    )
    @app_commands.describe(
        limit="Número máximo de PRs a mostrar (por defecto: 5)"
    )
    async def github_prs(
        self,
        interaction: discord.Interaction,
        limit: Optional[int] = 5
    ):
        """Muestra el estado de los pull requests abiertos en GitHub"""
        await interaction.response.defer()
        
        try:
            # Construir URL de la API de GitHub
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls"
            params = {
                'state': 'open',
                'sort': 'updated',
                'direction': 'desc',
                'per_page': min(limit, 10)  # Limitar a máximo 10
            }
            
            headers = {
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            # Añadir token si está disponible
            if self.github_token:
                headers['Authorization'] = f'Bearer {self.github_token}'
            
            # Hacer petición a la API
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error al obtener PRs: {response.status} - {error_text}")
                        embed = create_error_embed(
                            "Error al obtener PRs",
                            f"No se pudo conectar a la API de GitHub (Status: {response.status})"
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    prs = await response.json()
            
            # Crear embed con los PRs
            if not prs:
                embed = create_info_embed(
                    "Pull Requests",
                    "No hay pull requests abiertos en este momento."
                )
            else:
                embed = discord.Embed(
                    title=f"🔀 Pull Requests Abiertos ({len(prs)})",
                    description=f"Repositorio: **{self.repo_owner}/{self.repo_name}**",
                    color=0x3498db,
                    timestamp=datetime.now(timezone.utc)
                )
                
                for pr in prs:
                    pr_number = pr['number']
                    pr_title = pr['title']
                    pr_user = pr['user']['login']
                    pr_created = self._format_datetime(pr['created_at'])
                    pr_updated = self._format_datetime(pr['updated_at'])
                    pr_url = pr['html_url']
                    pr_draft = pr.get('draft', False)
                    pr_merged = pr.get('merged', False)
                    
                    # Estado del PR
                    status_emoji = self._get_status_emoji(pr['state'], pr_merged)
                    draft_text = " [DRAFT]" if pr_draft else ""
                    
                    # Formatear información
                    pr_info = (
                        f"{status_emoji} **[#{pr_number}]({pr_url})**{draft_text}\n"
                        f"👤 Autor: `{pr_user}`\n"
                        f"📅 Creado: {pr_created}\n"
                        f"🔄 Actualizado: {pr_updated}"
                    )
                    
                    # Añadir campo al embed (truncar título si es muy largo)
                    field_title = pr_title if len(pr_title) <= 50 else pr_title[:47] + "..."
                    embed.add_field(
                        name=field_title,
                        value=pr_info,
                        inline=False
                    )
                
                embed.set_footer(text=f"Mostrando {len(prs)} PR(s) más recientes")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener PRs de GitHub: {e}")
            embed = create_error_embed(
                "Error",
                f"Ocurrió un error al obtener los pull requests: {str(e)}"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(
        name="github_deployments",
        description="Ver el estado de los deployments recientes (workflow runs)"
    )
    @app_commands.describe(
        limit="Número máximo de deployments a mostrar (por defecto: 5)"
    )
    async def github_deployments(
        self,
        interaction: discord.Interaction,
        limit: Optional[int] = 5
    ):
        """Muestra el estado de los workflow runs recientes en GitHub"""
        await interaction.response.defer()
        
        try:
            # Construir URL de la API de GitHub
            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
            params = {
                'per_page': min(limit, 10)  # Limitar a máximo 10
            }
            
            headers = {
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
            
            # Añadir token si está disponible
            if self.github_token:
                headers['Authorization'] = f'Bearer {self.github_token}'
            
            # Hacer petición a la API
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error al obtener workflow runs: {response.status} - {error_text}")
                        embed = create_error_embed(
                            "Error al obtener deployments",
                            f"No se pudo conectar a la API de GitHub (Status: {response.status})"
                        )
                        await interaction.followup.send(embed=embed, ephemeral=True)
                        return
                    
                    data = await response.json()
                    runs = data.get('workflow_runs', [])
            
            # Crear embed con los workflow runs
            if not runs:
                embed = create_info_embed(
                    "Workflow Runs",
                    "No hay workflow runs disponibles en este momento."
                )
            else:
                embed = discord.Embed(
                    title=f"🚀 Deployments Recientes ({len(runs)})",
                    description=f"Repositorio: **{self.repo_owner}/{self.repo_name}**",
                    color=0x9b59b6,
                    timestamp=datetime.now(timezone.utc)
                )
                
                for run in runs:
                    run_id = run['id']
                    run_name = run['name']
                    run_status = run['status']
                    run_conclusion = run.get('conclusion')
                    run_branch = run['head_branch']
                    run_created = self._format_datetime(run['created_at'])
                    run_url = run['html_url']
                    run_actor = run['actor']['login']
                    
                    # Estado del workflow
                    status_emoji = self._get_workflow_emoji(run_status, run_conclusion)
                    
                    # Formatear estado
                    if run_status == "completed":
                        status_text = f"{run_conclusion.upper() if run_conclusion else 'COMPLETED'}"
                    else:
                        status_text = run_status.upper()
                    
                    # Formatear información
                    run_info = (
                        f"{status_emoji} **Estado:** {status_text}\n"
                        f"🌿 Branch: `{run_branch}`\n"
                        f"👤 Ejecutado por: `{run_actor}`\n"
                        f"📅 Iniciado: {run_created}\n"
                        f"🔗 [Ver detalles]({run_url})"
                    )
                    
                    # Añadir campo al embed (truncar nombre si es muy largo)
                    field_title = f"#{run_id}: {run_name}"
                    if len(field_title) > 50:
                        field_title = field_title[:47] + "..."
                    
                    embed.add_field(
                        name=field_title,
                        value=run_info,
                        inline=False
                    )
                
                embed.set_footer(text=f"Mostrando {len(runs)} workflow run(s) más recientes")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error al obtener workflow runs de GitHub: {e}")
            embed = create_error_embed(
                "Error",
                f"Ocurrió un error al obtener los deployments: {str(e)}"
            )
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    """Función para cargar el cog"""
    await bot.add_cog(GitHubStatusCog(bot))
    logger.info("GitHubStatusCog cargado")
