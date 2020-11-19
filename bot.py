# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    bot.py                                             :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: bbellavi <bbellavi@student.42.fr>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2020/11/16 06:16:50 by bbellavi          #+#    #+#              #
#    Updated: 2020/11/19 03:11:53 by bbellavi         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import os
import hashlib
import discord
import subprocess
import yaml


with open("config.yaml", "r") as f:
	config = yaml.load(f, Loader=yaml.FullLoader)

TOKEN			= config["bot"]["API_KEY"]
CWD				= os.getcwd()
POLL_DIR		= "poll"
EXEC_ROLES		= config["server"]["scope"]["roles"]
EXEC_CHANNELS 	= config["server"]["scope"]["channels"]
TIMEOUT			= int(config["exec"]["timeout"])

with open("context.yaml", "r") as f:
	CONTEXT = yaml.load(f, Loader=yaml.FullLoader)

class TheExecutor(discord.Client):
	async def on_ready(self):
		print(f"{self.user} has connected to Discord!")

	def _is_exec_channel(self, channel_id):
		"""

		Check if the channel id passed in parameter is an execute channel.

		Args:
			channel_id [str]: the channel id.

		Returns:
			[bool]: Returns True if channel_id is an execute channel otherwise False.
		"""		
		return channel_id in EXEC_CHANNELS

	def _is_exec_role(self, rolename):
		"""
		
		Check if role is an execute role.

		Args:
			rolename [str]: The rolename to check.

		Returns:
			[bool]: Returns True if rolename is an execute role, False otherwise.
		"""		
		return rolename in EXEC_ROLES

	def _is_valid_executor(self, roles, channel_id):
		"""
		
		Check if role and channel id are valid executor.

		Args:
			roles [str]: [description]
			channel_id [str]: [description]

		Returns:
			[bool]: True if is a valid executor, False otherwise.
		"""		
		is_exec = self._is_exec_channel(channel_id)
		is_role = any(self._is_exec_role(role) for role in roles)
		return is_exec and is_role

	def _is_markdowned(self, content):
		"""
		
		Check if content is markdown as described by discord.

		Args:
			content [str]: The content to be checked.

		Returns:
			[bool]: Returns True if content is markdowned, False otherwise.
		"""		
		return content.startswith("```") and content.endswith("```")

	def _is_runnable(self, content):
		"""

		Check if content is runnable, to be runnable, content must be
		followed by the `!run' command, 

		Args:
			content [str]: The content to be checked.

		Returns:
			[bool]: True if is runnable, False otherwise.
		"""		
		return content.endswith("!run")

	def _get_command(self, filename, context):
		"""

		Build docker command.

		Args:
			filename [str]: Filename of the file to be executed.
			context [dict]: Context describing language.

		Returns:
			[str]: The docker command.
		"""		
		return f"docker run -it --rm -v {CWD}/{POLL_DIR}:/tmp/{POLL_DIR} -w /tmp/{POLL_DIR} {context['image']} {context['interpreter']} {filename}"

	def _execute_command(self, command):
		"""
			Execute the command passed in parameter with subprocess call.

		Args:
			command [str]: command to be executed
		
		Returns:
			[str, bool] --	returns a tupples composed of :
			- [str] : result of the command
			- [bool] : True if an error occured, False otherwise
		"""
		process = subprocess.run(command, capture_output=True, timeout=TIMEOUT)
		error = False

		try:
			if process.returncode != 0:
				result = "Error : " + process.stderr.decode() if process.stderr else process.stdout.decode()
				error = True
			else:
				result = process.stdout.decode()
			
		except subprocess.TimeoutExpired:
			result = "Time limit exceeded"
			error = True
		
		return result, error

	def _execute_interpreted(self, filename, context):
		"""

		Execute interpreted language.

		Args:
			filename [str]: Filename of the file to execute.
			context [dict]: Context describing language.

		Returns:
			[str]: The result of the execution of the file.
		"""
		fullname = f"{POLL_DIR}/{filename}"
		command = self._get_command(filename, context).split()
		result, error = self._execute_command(command)

		os.remove(fullname)
		if error:
			return result
			
		if context['interpreter'] == "php":
			result = result[2:]

		return result

	def _execute_compiled(self, filename, context):
		"""

		Execute compiled language.

		Args:
			filename [str]: Filename of the file to execute.
			context [dict]: Context describing language.

		Returns:
			[str]: The result of the execution of the file.
		"""
		fullname = f"{POLL_DIR}/{filename}"
		command = self._get_command(filename, context).split()
		result, error = self._execute_command(command)

		os.remove(fullname)
		if error:
			return result

		command = f"docker run -it --rm -v {CWD}/{POLL_DIR}:/tmp/{POLL_DIR} -w /tmp/{POLL_DIR} {context['image']} ./a.out".split()
		result, error = self._execute_command(command)
		os.remove(f"{POLL_DIR}/a.out")

		return result

	def _execute(self, filename, context):
		"""[summary]

		Execute the file passed in parameter.

		Args:
			filename [str]: Filename of the file to execute.
			context [dict]: Context describing the language.

		Returns:
			[str]: The result of the execution of the file.
		"""		

		if context['interpreted']:
			return self._execute_interpreted(filename, context)
		
		if not context['interpreted']:
			return self._execute_compiled(filename, context)
		
		return "Language not supported."

	async def on_message(self, message):
		if not os.path.exists(POLL_DIR):
			os.mkdir(POLL_DIR)

		roles = [role.name for role in message.author.roles]
		channel_id = str(message.channel.id)
		content = message.content

		if self._is_valid_executor(roles, channel_id):

			if self._is_runnable(content):
				content = content[:-4]

				if self._is_markdowned(content):
					ext_len = content.find('\n') - 3
					extension = content[3:][:ext_len].strip()

					if extension in CONTEXT.keys():
						skip_len = len(extension) + 3
						content = content[skip_len:-3].strip()

						msg_hash = hashlib.sha256(f"{content + str(message.id)}".encode()).hexdigest()
						filename = f"{msg_hash}.{extension}"
						fullname = f"{POLL_DIR}/{filename}"
						
						with open(fullname, 'w') as f:
							f.write(content)

						result = self._execute(filename, CONTEXT[extension])

						if len(result) >= 2000:
							result = result[:200]

						await message.channel.send(f"```md\n{result}\n```")

TheExecutor().run(TOKEN)
