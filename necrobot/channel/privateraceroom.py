# Derived class; makes a private race room

import discord

from .raceroom import RaceRoom
from ..command import privaterace
from ..race import permissioninfo
from ..util import writechannel


class PrivateRaceRoom(RaceRoom):
    def __init__(self, race_manager, race_discord_channel, race_private_info, admin_as_member):
        RaceRoom.__init__(self, race_manager, race_discord_channel, race_private_info.race_info)
        self._room_creator = admin_as_member

        self.permission_info = permissioninfo.get_permission_info(self.necrobot.server, race_private_info)
        if admin_as_member not in self.permission_info.admins:
            self.permission_info.admins.append(admin_as_member)

        self.command_types.append(privaterace.Add(self))
        self.command_types.append(privaterace.Remove(self))
        self.command_types.append(privaterace.MakeAdmin(self))
        self.command_types.append(privaterace.ShowAdmins(self))
        self.command_types.append(privaterace.NoPost(self))
        self.command_types.append(privaterace.Post(self))

    # A string to add to the race details ("Private")
    @property
    def format_rider(self):
        return '(private)'

    # Sets up the leaderboard for the race
    async def initialize(self):
        # Set permissions -----------------------------------------
        read_permit = discord.Permissions.none()
        read_permit.read_messages = True

        # deny access to @everyone
        await self.deny(self.necrobot.server.default_role)

        # allow access for self
        await self.allow(self.necrobot.get_as_member(self.client.user))

        # give admin roles permission
        for role in self.permission_info.admin_roles:
            await self.allow(role)

        # give admins permission
        for member in self.permission_info.admins:
            await self.allow(member)

        # give racers permission
        for member in self.permission_info.racers:
            await self.allow(member)

        # Initialize base -----------------------------------------
        await RaceRoom.initialize(self)

        # Automatically enter creator into race
        await self.current_race.enter_member(self._room_creator)

    # Allow the member to see the channel
    async def allow(self, member_or_role):
        read_permit = discord.PermissionOverwrite()
        read_permit.read_messages = True
        await self.client.edit_channel_permissions(self.channel, member_or_role, read_permit)

    # Restrict the member from seeing the channel
    async def deny(self, member_or_role):
        read_deny = discord.PermissionOverwrite()
        read_deny.read_messages = False
        await self.client.edit_channel_permissions(self.channel, member_or_role, read_deny)

    # True if the user has admin permissions for this race
    def _virtual_is_admin(self, member):
        return self.permission_info.is_admin(member)

    # Close the channel.
    async def close(self):
        # If this is a CoNDOR race, log the room text before closing
        if self.race_info.condor_race:
            outfile_name = ''
            for racer in self.current_race.racers:
                outfile_name += '{0}-'.format(racer.member.display_name)
            outfile_name += str(self.channel.id)
            await writechannel.write_channel(self.client, self.channel, outfile_name)
        await self._race_manager.close_room(self)
