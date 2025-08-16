import discord
from discord import app_commands
from discord.ext import commands
from utils.database import db_manager

class OwnerControls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Create a command group for all admin commands
    admin_group = app_commands.Group(name="admin", description="Administrative role management commands")

    @admin_group.command(name="declare_role", description="Declare a role as administrative (Owner only)")
    async def declare_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        # Check if the user is the server owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can declare administrative roles!", ephemeral=True)
            return
        
        try:
            # Add the role to the database
            await db_manager.add_role(role.id)
            
            embed = discord.Embed(
                title="✅ Administrative Role Declared",
                description=f"The role **{role.name}** has been declared as administrative.",
                color=discord.Color.green()
            )
            embed.add_field(name="Role ID", value=str(role.id), inline=True)
            embed.add_field(name="Role Color", value=str(role.color), inline=True)
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error declaring role: {str(e)}", 
                ephemeral=True
            )

    @admin_group.command(name="list_roles", description="List all administrative roles")
    async def list_admin_roles(self, interaction: discord.Interaction):
        try:
            # Get all roles from the database
            role_ids = await db_manager.get_all_roles()
            
            if not role_ids:
                await interaction.response.send_message("📋 No administrative roles have been declared yet.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📋 Administrative Roles",
                description="Here are all the administrative roles:",
                color=discord.Color.blue()
            )
            
            for role_id in role_ids:
                role = interaction.guild.get_role(role_id)
                if role:
                    embed.add_field(
                        name=role.name,
                        value=f"ID: {role.id} | Color: {role.color}",
                        inline=False
                    )
                else:
                    # Role might have been deleted
                    embed.add_field(
                        name="Unknown Role",
                        value=f"ID: {role_id} (Role may have been deleted)",
                        inline=False
                    )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error listing roles: {str(e)}", 
                ephemeral=True
            )

    @admin_group.command(name="remove_role", description="Remove a role from administrative roles (Owner only)")
    async def remove_admin_role(self, interaction: discord.Interaction, role: discord.Role):
        # Check if the user is the server owner
        if interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Only the server owner can remove administrative roles!", ephemeral=True)
            return
        
        try:
            # Check if the role is actually administrative
            is_admin = await db_manager.check_role(role.id)
            if not is_admin:
                await interaction.response.send_message(f"❌ The role **{role.name}** is not currently administrative!", ephemeral=True)
                return
            
            # Remove the role from the database
            removed = await db_manager.remove_role(role.id)
            
            if removed:
                embed = discord.Embed(
                    title="🗑️ Administrative Role Removed",
                    description=f"The role **{role.name}** has been removed from administrative roles.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Role ID", value=str(role.id), inline=True)
                embed.add_field(name="Role Color", value=str(role.color), inline=True)
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"❌ Failed to remove role **{role.name}**", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Error removing role: {str(e)}", 
                ephemeral=True
            )
