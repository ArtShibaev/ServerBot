import asyncio
import logging
import random
import string
import time

import paramiko

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

ssh_user = 'root'

logging.basicConfig(level=logging.INFO)
dp = Dispatcher()
bot = Bot(token='6485242380:AAEWC26XKA8qMqneTYjw35GByXSW629Rj0Q', parse_mode=ParseMode.HTML)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname='194.32.248.209', username=ssh_user, password='opxAj0iB8R', look_for_keys=False, allow_agent=False)
ssh = client.invoke_shell()


def get_process_status():
    ssh.send('pm2 status\n')
    time.sleep(1)
    response = str(ssh.recv(3000))
    return 'running' if all(x in response for x in ['movies_website', 'online']) else 'stopped'


def default_keyboard(process_old_status=''):
    builder = InlineKeyboardBuilder()
    if not process_old_status:
        builder.row(types.InlineKeyboardButton(text='🔴 Остановить процесс' if get_process_status() == 'running' else '🟢 Запустить процесс', callback_data='manage_process'))
    elif process_old_status == 'running':
        builder.row(types.InlineKeyboardButton(text='🟢 Запустить процесс', callback_data='manage_process'))
    elif process_old_status == 'stopped':
        builder.row(types.InlineKeyboardButton(text='🔴 Остановить процесс', callback_data='manage_process'))
    builder.row(types.InlineKeyboardButton(text='🆙 Аптайм', callback_data='uptime'))
    builder.row(types.InlineKeyboardButton(text='🔄 Перезагрузить сервер', callback_data='reboot'))
    builder.row(types.InlineKeyboardButton(text='🗂️ Бэкапы', callback_data='backups'))
    builder.row(types.InlineKeyboardButton(text='🔑 Сбросить пароль администратора', callback_data='reset_password'))
    builder.adjust(2, 2)
    return builder.as_markup()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f'Этот бот позволяет контролировать корректность работы сервера.\n'
                         f'Для взаимодействия используй кнопки ниже.', reply_markup=default_keyboard())


@dp.callback_query(F.data == 'backups')
async def backups(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='Создать новый', callback_data='new_backup'))
    builder.row(types.InlineKeyboardButton(text='Восстановить из последнего', callback_data='restore_from_latest_backup'))
    builder.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='go_back'))
    builder.adjust(2, 2)
    await callback.message.answer(f'<b>Бэкапы</b>', reply_markup=builder.as_markup())


@dp.callback_query(F.data == 'new_backup')
async def new_backup(callback: types.CallbackQuery):
    ssh.send('cp -R movies_website backup\n')
    time.sleep(3)
    await callback.answer('Бэкап создан', show_alert=True)


@dp.callback_query(F.data == 'restore_from_latest_backup')
async def new_backup(callback: types.CallbackQuery):
    ssh.send('pm2 kill\n')
    time.sleep(1)
    ssh.send('rm -r movies_website\n')
    time.sleep(1)
    ssh.send('cd ~/backup\n')
    time.sleep(1)
    ssh.send('npm install\n')
    time.sleep(1)
    ssh.send('mv ~/backup ~/movies_website\n')
    time.sleep(7)
    ssh.send('cd ~/movies_wibsite\n')
    time.sleep(1)
    ssh.send('pm2 start app.js --name "movies_website" --watch && pm2 save\n')
    await callback.message.answer('Восстановлено из резервной копии\nПроцесс перезапущен')


@dp.callback_query(F.data == 'uptime')
async def uptime(callback: types.CallbackQuery):
    stdin, stdout, stderr = client.exec_command('pm2 status')
    pm2_status_output = stdout.read().decode('utf-8')
    lines = pm2_status_output.strip().split('\n')
    cleaned_output = [line for line in lines if not (line.startswith('┌') or line.startswith('├') or line.startswith('└'))]
    header = cleaned_output[0].split('│')[1:-1]
    data = cleaned_output[1].split('│')[1:-1]
    key_value_dict = {h.strip(): d.strip() for h, d in zip(header, data)}
    formatted_str = '\n'.join([f'{k}: {v}' for k, v in key_value_dict.items()])
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text='⬅️ Назад', callback_data='go_back'))
    await callback.message.edit_text(f'<pre>{formatted_str}</pre>', reply_markup=builder.as_markup())


@dp.callback_query(F.data == 'manage_process')
async def manage_process(callback: types.CallbackQuery):
    status = get_process_status()
    if status == 'running':
        ssh.send('pm2 stop 0\n')
        await callback.answer('Процесс остановлен', show_alert=True)
    elif status == 'stopped':
        ssh.send('pm2 start 0 --watch\n')
        await callback.answer('Процесс запущен', show_alert=True)
    await callback.message.edit_reply_markup(str(callback.message.message_id), reply_markup=default_keyboard(status))


@dp.callback_query(F.data == 'go_back')
async def backups(callback: types.CallbackQuery):
    await callback.message.edit_text(f'Этот бот позволяет контролировать корректность работы сервера.\n'
                                     f'Для взаимодействия используй кнопки ниже.')
    await callback.message.edit_reply_markup(str(callback.message.message_id), reply_markup=default_keyboard())


@dp.callback_query(F.data == 'reset_password')
async def handle_password_reset(callback: types.CallbackQuery):
    y = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(y) for _ in range(8))
    # ssh.send(f'echo "{password}" | passwd --stdin {ssh_user}')  # Это если захотим делать замену пароля
    await callback.message.reply(f'Пароль изменён: <code>{password}</code>')
    await callback.message.edit_reply_markup(str(callback.message.message_id), reply_markup=default_keyboard())


@dp.callback_query(F.data == 'reboot')
async def handle_password_reset(callback: types.CallbackQuery):
    ssh.send('reboot now\n')
    await callback.answer('Сервер перезагружается', show_alert=True)
    await callback.message.edit_reply_markup(str(callback.message.message_id), reply_markup=default_keyboard(process_old_status='running'))


async def check_status():
    while True:
        ssh.send('pm2 status\n')
        time.sleep(1)
        response = str(ssh.recv(3000))
        if 'errored' in response:
            await bot.send_message(422904706, 'В процессе возникла ошибка')
        time.sleep(30)


async def main() -> None:
    await check_status()
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
