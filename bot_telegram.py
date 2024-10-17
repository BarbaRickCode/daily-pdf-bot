import calendar
import os
from datetime import date
import logging
from logging import exception
from typing import List
from telegram.ext import filters


from genera_tabella import crea_tabella

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, CallbackContext, \
    MessageHandler

# Define states
(NAME, CITY, USER_ASSISTED, MONTH_AND_YEAR, SERVICE, ACTIVITY,
 ASK_WORKDAY, ADD_ANOTHER_SHIFT, ASK_EXCEPTIONS,
 SELECT_EXCEPTION_DAY, WORKED_ON_EXCEPTION_DAY,
 SELECT_EXCEPTION_REASON, MORE_EXCEPTIONS,
 EXCEPTIONS_SHIFT_START_HOUR,EXCEPTIONS_SHIFT_START_MINUTE, EXCEPTION_SHIFT_END_HOUR, EXCEPTION_SHIFT_END_MINUTE,
 EXCEPTION_CODE, ADD_ANOTHER_EXCEPTION_SHIFT,
 SHIFT_START_HOUR, SHIFT_START_MINUTE,
 SHIFT_END_HOUR, SHIFT_END_MINUTE) = range(23)

# Data for inline buttons
workers = ["Francesca Porcedda"]
users_assisted = [
    "Bruno Manca",
    "Maria Filomena Ibba",
    "Teodolinda Massa",
    "Michela Sanna",
    "Giancarlo Saba",
    "Vitalia Pitzus",
    "Teresa Grecu"
]
cities = ["Serrenti"]
services = ["SAD", "L. 162/98"]
activities = [
    "A1: igiene personale", "A2: igiene ambiente", "A3: accompagnamento/assist. extradomiciliare",
    "A4: preparazione e/o somministrazione pasti", "B1: disbrigo pratiche", "B2: programmazione",
    "C1: aiuto somministrazione terapia", "C2: supporto emotivo/socializzazione"
]
days_of_the_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]

def mese_nome_a_numero(nome_mese):
    """
    Converte il nome del mese in numero.

    :param nome_mese: Il nome del mese in italiano (es. "Gennaio").
    :return: Il numero del mese corrispondente, o None se il mese non è valido.
    """
    mesi = {
        "Gennaio": 1,
        "Febbraio": 2,
        "Marzo": 3,
        "Aprile": 4,
        "Maggio": 5,
        "Giugno": 6,
        "Luglio": 7,
        "Agosto": 8,
        "Settembre": 9,
        "Ottobre": 10,
        "Novembre": 11,
        "Dicembre": 12
    }
    return mesi.get(nome_mese)


# Function to get the current and previous month names
def get_previous_month_and_year() -> dict:
    today = date.today()
    current_month = today.month
    current_year = today.year

    # Calcola il mese precedente
    if current_month == 1:
        previous_month = 12
        previous_year = current_year - 1  # Decrementa l'anno se siamo a gennaio
    else:
        previous_month = current_month - 1
        previous_year = current_year

    # Lista dei nomi dei mesi in italiano
    month_names = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]

    previous_month_name = month_names[previous_month - 1]

    return {
        "previous_month": previous_month_name,
        "previous_year": previous_year
    }


def get_current_month_and_year() -> dict:
    today = date.today()
    current_month = today.month
    current_year = today.year

    # Lista dei nomi dei mesi in italiano
    month_names = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]

    current_month_name = month_names[current_month - 1]

    return {
        "current_month": current_month_name,
        "current_year": current_year
    }

async def sticker_handler(update: Update, context: CallbackContext) -> None:
    # Check if the message contains a sticker
    if update.message and update.message.sticker:
        sticker_file_id = update.message.sticker.file_id  # Get the sticker file ID
        await update.message.reply_text(f"Sticker ID: {sticker_file_id}")

# Example function to send a sticker
async def send_sticker(update: Update, context: CallbackContext) -> None:
    # Replace 'STICKER_FILE_ID' with the actual sticker file ID you want to send
    sticker_file_id = 'STICKER_FILE_ID'

    await update.message.reply_sticker(sticker_file_id)
async def start(update: Update, context: CallbackContext) -> int:
    try:
        # Send a sticker
        sticker_file_id = 'CAACAgIAAxkBAAIVsGcP-1u3dPAXpmdpRw2zsBjqSCPwAAIBAQACVp29CiK-nw64wuY0NgQ'  # Replace with your sticker's file ID
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_file_id)
        await update.message.reply_text("Benvenuta/o!\nIniziamo a raccogliere i dati per compilare la tua giornaliera.")
        return await worker_name(update, context)
    except Exception as e:
        logger.error(f"Error in start function: {e}")
        await update.message.reply_text("Si è verificato un errore. Riprova per favore.")
        return ConversationHandler.END  # Or an appropriate error handling state



# Function to ask for the worker's name
async def worker_name(update: Update, context: CallbackContext) -> int:
    # Create a keyboard with the names of the workers
    keyboard = [[InlineKeyboardButton(worker, callback_data=worker)] for worker in workers]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Ask the user to select the name of the worker
    await update.message.reply_text("Seleziona il nome dell'operatore:", reply_markup=reply_markup)

    # Wait for the user's response
    return NAME


# Handle the worker name selection
async def handle_worker_name(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    selected_worker = query.data

    # Save the selected name
    context.user_data['selected_worker'] = selected_worker

    # Confirm the selection and move to the next state (CITY)
    await query.answer()
    await query.edit_message_text(f"Hai selezionato: {selected_worker}")

    # Ask for the city
    return await service(update, context)


async def service(update: Update, context: CallbackContext) -> int:
    keyboard = [[InlineKeyboardButton(service, callback_data=service)] for service in services]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Seleziona il servizio:", reply_markup=reply_markup)

    # Wait for the service response
    return SERVICE


async def handle_service(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    service = query.data

    # Save the selected user assisted
    context.user_data['service'] = service

    await query.answer()
    await query.edit_message_text(f"Hai selezionato: {service}")

    # Ask for the month
    return await city(update, context)


# Function to ask for the city
async def city(update: Update, context: CallbackContext) -> int:
    keyboard = [[InlineKeyboardButton(city, callback_data=city)] for city in cities]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Seleziona il paese:", reply_markup=reply_markup)

    # Wait for the city response
    return CITY


# Handle the city selection
async def handle_city(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    selected_city = query.data

    # Save the selected city
    context.user_data['selected_city'] = selected_city

    # Confirm the selection and move to the next state (USER_ASSISTED)
    await query.answer()
    await query.edit_message_text(f"Hai selezionato: {selected_city}")

    # Ask for the user
    return await user_assisted(update, context)


# Function to ask for the user assisted
async def user_assisted(update: Update, context: CallbackContext) -> int:
    keyboard = [[InlineKeyboardButton(user_assisted, callback_data=user_assisted)] for user_assisted in users_assisted]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Seleziona l'utente:", reply_markup=reply_markup)

    # Wait for the users response
    return USER_ASSISTED


# Handle user assisted
async def handle_user_assisted(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    user_assisted = query.data

    # Save the selected user assisted
    context.user_data['user_assisted'] = user_assisted

    await query.answer()
    await query.edit_message_text(f"Hai selezionato: {user_assisted}")

    # Ask for the service
    return await activity(update, context)


async def activity(update: Update, context: CallbackContext) -> int:
    keyboard = [[InlineKeyboardButton(activity, callback_data=activity)] for activity in activities]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Seleziona il codice attività:", reply_markup=reply_markup)

    # Wait for the service response
    return ACTIVITY


async def handle_activity(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    activity = query.data

    # Save the selected user assisted
    context.user_data['activity'] = activity

    await query.answer()
    await query.edit_message_text(f"Hai selezionato: {activity}")

    # Ask for the month
    return await ask_month_and_year(update, context)


# async def monthOld(update: Update, context: CallbackContext) -> int:
#     # Get the current and previous month dynamically
#     months = get_current_and_previous_month()
#
#     # Create inline buttons with the month options
#     keyboard = [[InlineKeyboardButton(month, callback_data=month)] for month in months]
#     reply_markup = InlineKeyboardMarkup(keyboard)
#
#     # Ask the user to select the month
#     await update.callback_query.message.reply_text("Seleziona il mese di riferimento:", reply_markup=reply_markup)
#
#     # Stay in the MONTH state awaiting response
#     return MONTH

async def ask_month_and_year(update: Update, context: CallbackContext) -> int:
    # Ottieni il mese e l'anno corrente e quello precedente
    current_month_and_year = get_current_month_and_year()
    previous_month_and_year = get_previous_month_and_year()

    # Crea le opzioni della tastiera utilizzando le stringhe per callback_data
    keyboard = [
        [
            InlineKeyboardButton(
                f"{current_month_and_year['current_month']} {current_month_and_year['current_year']}",
                callback_data=f"{current_month_and_year['current_month']}_{current_month_and_year['current_year']}"
            ),
            InlineKeyboardButton(
                f"{previous_month_and_year['previous_month']} {previous_month_and_year['previous_year']}",
                callback_data=f"{previous_month_and_year['previous_month']}_{previous_month_and_year['previous_year']}"
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Chiedi all'utente di selezionare il mese
    await update.callback_query.message.reply_text("Seleziona il mese di riferimento:", reply_markup=reply_markup)

    # Resta nello stato MONTH in attesa di una risposta
    return MONTH_AND_YEAR


def save_month_and_year(context: CallbackContext, month_str: str, year_str: str):
    month_int = mese_nome_a_numero(month_str)  # Converti il mese in int
    year_int = int(year_str)  # Converti l'anno in int

    # Salva nel contesto
    context.user_data['selected_month_int'] = month_int
    context.user_data['selected_year_int'] = year_int
    context.user_data['selected_month_str'] = month_str
    context.user_data['selected_year_str'] = year_str



async def handle_month_and_year(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()  # Rispondi subito al callback

    # Stampa il valore di query.data per debug
    logger.info(f"Received callback data: {query.data}")  # Log per vedere i dati ricevuti

    selected_month_and_year = query.data.split('_')  # Divide il dato in mese e anno

    # Stampa il valore di selected_month_and_year per debug
    logger.info(f"Split month and year: {selected_month_and_year}")  # Log per il risultato della divisione

    if len(selected_month_and_year) != 2:
        await query.edit_message_text("Formato dei dati non valido. Riprova.")
        return MONTH_AND_YEAR  # Torna allo stato di richiesta del mese e anno

    selected_month = selected_month_and_year[0]
    selected_year = selected_month_and_year[1]

    # Salva nel contesto
    context.user_data['selected_month_str'] = selected_month
    context.user_data['selected_year_str'] = selected_year
    context.user_data['selected_month_int'] = mese_nome_a_numero(selected_month)
    context.user_data['selected_year_int'] = int(selected_year)

    # Stampa i valori di selected_month e selected_year per debug
    logger.info(f"Value: {context.user_data['selected_month_str']},"
                f"Value: {context.user_data['selected_year_str']},"
                f"Value: {context.user_data['selected_month_int']},"
                f"Value: {context.user_data['selected_year_int']}, ")

    # Salva il mese e l'anno nel contesto
    save_month_and_year(context, selected_month, selected_year)

    # Conferma la selezione
    await query.edit_message_text(f"Hai selezionato: {selected_month} {selected_year}")

    # Procedi a chiedere altre informazioni
    return await ask_workday(update, context)



# Function to ask if the user worked on a specific day
async def ask_workday(update: Update, context: CallbackContext) -> int:
    # Get the current day to ask about
    day_index = context.user_data.get('current_day_index', 0)
    day = days_of_the_week[day_index]

    # Ask if the user worked that day (callback_query must be used here, not message)
    keyboard = [[InlineKeyboardButton("Sì", callback_data="yes"), InlineKeyboardButton("No", callback_data="no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Use callback_query to respond to the user's input properly
    await update.callback_query.message.reply_text(f"Hai lavorato {day}?", reply_markup=reply_markup)

    return ASK_WORKDAY

# Handle the user's response for whether they worked
async def handle_workday_response(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    # Get the day and save it
    day_index = context.user_data.get('current_day_index', 0)
    day = days_of_the_week[day_index]

    if query.data == "yes":
        # If they worked, ask for the shift start time
        return await ask_shift_start_hour(update, context)
    else:
        # If they didn't work, save an empty entry for the day
        shifts = context.user_data.setdefault('weekly_shifts', {})
        shifts.setdefault(day, [])  # Create an empty list for the day

        # Move to the next day
        return await next_day(update, context)

async def hours_keyboard() -> [[InlineKeyboardButton]]:
    hours = [str(hour).zfill(2) for hour in range(24)]  # Hours from 00 to 23
    return [[InlineKeyboardButton(hours[i], callback_data=hours[i]) for i in range(j, j + 6)] for j in
     range(0, 24, 6)]

async def minutes_keyboard() -> [[InlineKeyboardButton]]:
    # Define the minutes: 00, 15, 30, 45
    minutes = ['00', '15', '30', '45']
    return [[InlineKeyboardButton(minute, callback_data=minute) for minute in minutes]]

async def ask_shift_start_hour(update: Update, context: CallbackContext) -> int:
    reply_markup = InlineKeyboardMarkup(await hours_keyboard())
    await update.callback_query.message.reply_text("Seleziona l'ora di inizio del turno:", reply_markup=reply_markup)

    return SHIFT_START_HOUR  # New state for start hour selection


async def handle_shift_start_hour(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    shift_start_hour = query.data  # Get the selected hour

    # Save the start hour in the context
    context.user_data['shift_start_hour'] = shift_start_hour

    await query.answer()
    await update.callback_query.message.reply_text(
        f"Hai selezionato l'orario di inizio: {shift_start_hour}.\n Ora seleziona i minuti:")

    return await ask_shift_start_minute(update, context)


async def ask_shift_start_minute(update: Update, context: CallbackContext) -> int:
    reply_markup = InlineKeyboardMarkup(await minutes_keyboard())
    await update.callback_query.message.reply_text("Seleziona i minuti per l'orario di inizio:",
                                                   reply_markup=reply_markup)

    return SHIFT_START_MINUTE  # New state for start minute selection


async def handle_shift_start_minute(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    shift_start_minute = query.data  # Get the selected minute

    # Save the start minute in the context
    context.user_data['shift_start_minute'] = shift_start_minute

    await query.answer()
    await update.callback_query.message.reply_text(
        f"Hai selezionato l'orario di inizio: {context.user_data['shift_start_hour']}:{shift_start_minute}.")

    # Now ask for shift end hour
    return await ask_shift_end_hour(update, context)


async def ask_shift_end_hour(update: Update, context: CallbackContext) -> int:
    reply_markup = InlineKeyboardMarkup(await hours_keyboard())
    await update.callback_query.message.reply_text("Seleziona l'ora di fine del turno:", reply_markup=reply_markup)

    return SHIFT_END_HOUR  # New state for end hour selection


async def handle_shift_end_hour(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    shift_end_hour = query.data  # Get the selected hour for end shift

    # Save the end hour in the context
    context.user_data['shift_end_hour'] = shift_end_hour

    await query.answer()
    await update.callback_query.message.reply_text(
        f"Hai selezionato l'orario di fine: {shift_end_hour}:00.\n Ora seleziona i minuti:")

    return await ask_shift_end_minute(update, context)


async def ask_shift_end_minute(update: Update, context: CallbackContext) -> int:
    reply_markup = InlineKeyboardMarkup(await minutes_keyboard())
    await update.callback_query.message.reply_text("Seleziona i minuti per l'orario di fine:",
                                                   reply_markup=reply_markup)

    return SHIFT_END_MINUTE  # New state for end minute selection


# Function to handle the shift end minute and format the shift
async def handle_shift_end_minute(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    shift_end_minute = query.data  # Get the selected minute for end shift

    # Save the end minute in the context
    context.user_data['shift_end_minute'] = shift_end_minute

    await query.answer()

    # Combine start and end times into a shift string
    shift_start_hour = context.user_data['shift_start_hour']
    shift_start_minute = context.user_data['shift_start_minute']
    shift_end_hour = context.user_data['shift_end_hour']

    # Format the shift string
    shift_str = f"{shift_start_hour}:{shift_start_minute} - {shift_end_hour}:{shift_end_minute}"

    # Store the shift in the weekly shifts for the current day
    day_index = context.user_data.get('current_day_index', 0)
    day = days_of_the_week[day_index]

    shifts = context.user_data.setdefault('weekly_shifts', {})
    shifts.setdefault(day, []).append(shift_str)  # Append the formatted shift string

    await update.callback_query.message.reply_text(
        f"Hai selezionato l'orario di fine: {shift_end_hour}:{shift_end_minute}.\n"
        f"Turno registrato: {shift_str}."
    )

    # Check if the user wants to add another shift
    return await ask_add_another_shift(update, context)  # Ask if they want to add another shift


# Function to ask if the user wants to add another shift
async def ask_add_another_shift(update: Update, context: CallbackContext) -> int:
    keyboard = [[InlineKeyboardButton("Sì", callback_data="yes"), InlineKeyboardButton("No", callback_data="no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Hai lavorato un altro turno lo stesso giorno?",
                                                   reply_markup=reply_markup)
    return ADD_ANOTHER_SHIFT


# Handle the user's response for adding another shift
async def handle_add_another_shift(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query.data == "yes":
        # Ask for another shift start time
        return await ask_shift_start_hour(update, context)
    else:
        # Move to the next day
        return await next_day(update, context)


# Function to move to the next day
async def next_day(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    # Increment the current day index
    context.user_data['current_day_index'] = context.user_data.get('current_day_index', 0) + 1

    # Check if all days have been processed
    if context.user_data['current_day_index'] < len(days_of_the_week):
        return await ask_workday(update, context)
    else:
        context.user_data['current_day_index'] = 0
        return await ask_work_exceptions(update, context)


async def ask_work_exceptions(update: Update, context: CallbackContext) -> int:
    # Ask the user if they had any exceptions during the month
    keyboard = [[InlineKeyboardButton("Sì", callback_data="yes"), InlineKeyboardButton("No", callback_data="no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Use callback_query to send the message
    await update.callback_query.message.reply_text("Hai avuto eccezioni lavorative questo mese?",
                                                   reply_markup=reply_markup)

    return ASK_EXCEPTIONS  # This state will handle the user's response


async def handle_work_exceptions(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query.data == "yes":
        # Initialize the work_exceptions dictionary
        context.user_data['work_exceptions'] = {}
        # Prompt the user to select a day with exceptions
        return await ask_exception_day(update, context)
    else:
        # If no exceptions, end data collection
        await query.answer()
        await update.callback_query.message.reply_text("Grazie, la raccolta dati è completa.")
        return await show_final_data (update, context)


async def ask_exception_day(update: Update, context: CallbackContext) -> int:

    # Ottieni il mese e l'anno selezionati
    selected_month = context.user_data['selected_month_int']
    selected_year = context.user_data['selected_year_int']

    # Calcola il numero di giorni nel mese
    num_days = calendar.monthrange(selected_year, selected_month)[1]

    # Crea i pulsanti per ogni giorno del mese
    keyboard = []
    row = []  # Lista temporanea per i pulsanti della riga
    for day in range(1, num_days + 1):
        # Calcola il giorno della settimana per il giorno corrente
        week_day_index = calendar.weekday(selected_year, selected_month, day)  # Ottieni l'indice del giorno della settimana
        week_day_name = days_of_the_week[week_day_index][:3]  # Prendi il nome abbreviato (es. Lun, Mar)

        # Aggiungi il pulsante alla riga
        row.append(InlineKeyboardButton(f"{day} {week_day_name}", callback_data=str(day)))

        # Aggiungi la riga al keyboard se ha raggiunto il numero massimo di tasti (4 in questo caso)
        if len(row) == 4:
            keyboard.append(row)
            row = []  # Reset della riga per il prossimo set di pulsanti

    # Aggiungi eventuali pulsanti rimanenti alla tastiera
    if row:
        keyboard.append(row)

    # Crea la tastiera a colonne multiple per visualizzarne di più in una volta
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Seleziona il giorno con eccezioni:", reply_markup=reply_markup)
    return SELECT_EXCEPTION_DAY  # Handle the day selection next


async def handle_exception_day(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    selected_day = query.data

    # Save the selected day
    context.user_data['current_exception_day'] = selected_day

    # Ask if the user worked on this day
    keyboard = [[InlineKeyboardButton("Sì", callback_data="yes"), InlineKeyboardButton("No", callback_data="no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text(f"Hai lavorato {selected_day}?", reply_markup=reply_markup)
    return WORKED_ON_EXCEPTION_DAY


async def handle_worked_on_exception_day(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query.data == "yes":
        # Proceed to ask for work shifts (same logic as asking for regular workday)
        return await ask_exception_shifts_start_hour(update, context)
    else:
        # Ask for the exception reason
        return await ask_exception_code(update, context)


# Funzione per chiedere i turni in un giorno di eccezione
async def ask_exception_shifts_start_hour(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    # Ottieni il giorno di eccezione corrente
    exception_day = context.user_data['current_exception_day']
    reply_markup = InlineKeyboardMarkup(await hours_keyboard())

    await update.callback_query.message.reply_text(f"Seleziona l'orario di inizio per il giorno di eccezione {exception_day}:", reply_markup=reply_markup)

    return EXCEPTIONS_SHIFT_START_HOUR

# Ensure consistent variable names
async def handle_exception_shift_start_hour(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    exception_shift_start_hour = query.data  # Get the selected hour

    context.user_data['exception_shift_start_hour'] = exception_shift_start_hour
    await query.answer()
    await update.callback_query.message.reply_text(
        f"Hai selezionato l'orario di inizio: {exception_shift_start_hour}.\n Ora seleziona i minuti:"
    )

    return await ask_exception_shift_start_minute(update, context)

async def ask_exception_shift_start_minute(update: Update, context: CallbackContext) -> int:
    reply_markup = InlineKeyboardMarkup(await minutes_keyboard())
    await update.callback_query.message.reply_text("Seleziona i minuti per l'orario di inizio:",
                                                   reply_markup=reply_markup)
    return EXCEPTIONS_SHIFT_START_MINUTE  # New state for start minute selection


async def handle_exception_shift_start_minute(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    exception_shift_start_minute = query.data  # Get the selected minute

    # Save the start minute in the context
    context.user_data['exception_shift_start_minute'] = exception_shift_start_minute

    await query.answer()
    await update.callback_query.message.reply_text(
        f"Hai selezionato l'orario di inizio: {context.user_data['exception_shift_start_hour']}:{exception_shift_start_minute}.")

    # Now ask for shift end hour
    return await ask_shift_exception_end_hour(update, context)


async def ask_shift_exception_end_hour(update, context):
    reply_markup = InlineKeyboardMarkup(await hours_keyboard())
    await update.callback_query.message.reply_text("Seleziona l'ora di fine del turno:", reply_markup=reply_markup)

    return EXCEPTION_SHIFT_END_HOUR  # New state for end hour selection


# Gestisce l'orario di inizio per un giorno di eccezione
async def ask_exception_shift_end_minute(update, context):
    reply_markup = InlineKeyboardMarkup(await minutes_keyboard())
    await update.callback_query.message.reply_text("Seleziona i minuti per l'orario di fine turno:",
                                                   reply_markup=reply_markup)
    return EXCEPTION_SHIFT_END_MINUTE  # New state for start minute selection


async def handle_exception_shift_end_hour(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    shift_exception_end_hour = query.data  # Ottieni l'ora della fine del turno

    # Salva l'orario di fine turno per il giorno di eccezione
    context.user_data['exception_shift_end_hour'] = shift_exception_end_hour
    await update.callback_query.message.reply_text(
        f"Hai selezionato l'orario di fine turno: {shift_exception_end_hour}.\n Ora seleziona i minuti:")

    return await ask_exception_shift_end_minute(update, context)

    # Combine start and end times into a shift string accurately
async def handle_exception_shift_end_minute(update: Update, context: CallbackContext) -> int:
        query = update.callback_query
        exception_shift_end_minute = query.data  # Get the selected minute for end shift

        context.user_data['exception_shift_end_minute'] = exception_shift_end_minute
        await query.answer()

        # Combine start and end times into a shift string
        shift_str = (
            f"{context.user_data['exception_shift_start_hour']}:{context.user_data['exception_shift_start_minute']} "
            f"- {context.user_data['exception_shift_end_hour']}:{exception_shift_end_minute}"
        )

        # Store the shift in the work_exceptions for the current day
        exception_day = int(context.user_data['current_exception_day'])  # Convert to integer
        work_exceptions = context.user_data.setdefault('work_exceptions', {})
        work_exceptions.setdefault(exception_day, []).append(shift_str)  # Append the formatted shift string

        await update.callback_query.message.reply_text(
            f"Hai selezionato l'orario di fine: {context.user_data['exception_shift_end_hour']}:{exception_shift_end_minute}.\n"
            f"Turno registrato: {shift_str}."
        )

        return await ask_add_another_exception_shift(update, context)

async def ask_add_another_exception_shift(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    # Crea una tastiera per chiedere se si vuole aggiungere un altro turno
    keyboard = [[InlineKeyboardButton("Sì", callback_data="yes"), InlineKeyboardButton("No", callback_data="no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text("Vuoi aggiungere un altro turno per questo giorno?", reply_markup=reply_markup)

    return ADD_ANOTHER_EXCEPTION_SHIFT


# Gestisce la risposta dell'utente riguardo l'aggiunta di un altro turno
async def handle_add_another_exception_shift(update: Update, context: CallbackContext) -> int:
    query = update.callback_query

    if query.data == "yes":
        # L'utente ha scelto di aggiungere un altro turno, quindi chiedi l'orario di inizio
        return await ask_exception_shifts_start_hour(update, context)
    else:
        # L'utente non vuole aggiungere altri turni
        return await  ask_work_exceptions(update, context)


# Function to ask about the reason for a work exception
async def ask_exception_code(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()

    # List of predefined exceptions
    exceptions = [
        "PR: Permesso Recupero", "FE: Ferie", "R: Recupero", "P: Permesso",
        "ST: Straordinario", "MA: Malattia", "LD: Lavoro Domenicale",
        "PN: Permesso NON Retribuito", "PL: Permesso Lutto", "VM: Visita Medica", "S: Sostituzione"
    ]

    # Create a keyboard with the exception codes
    keyboard = [[InlineKeyboardButton(exception, callback_data=exception)] for exception in exceptions]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Ask the user to select an exception reason
    await update.callback_query.message.reply_text("Seleziona un codice eccezione per il giorno non lavorato:",
                                                   reply_markup=reply_markup)

    # Return the state to handle the exception code
    return EXCEPTION_CODE  # Updated state name


async def handle_exception_code(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    selected_code = query.data

    # Ottieni il giorno corrente
    exception_day = int(context.user_data['current_exception_day'])  # Converti in intero

    # Salva il codice di eccezione nel dizionario comune `work_exceptions`
    work_exceptions = context.user_data.setdefault('work_exceptions', {})

    if exception_day not in work_exceptions:
        work_exceptions[exception_day] = []  # Inizializza come lista se non esiste già

    # Aggiungi il codice di eccezione alla lista
    work_exceptions[exception_day].append(selected_code)  # Aggiungi il codice direttamente

    await query.answer()
    await query.message.reply_text(f"Eccezione registrata per il giorno {exception_day}: {selected_code}")

    # Chiedi se ci sono altre eccezioni
    return await ask_more_exceptions(update, context)

async def ask_more_exceptions(update: Update, context: CallbackContext) -> int:
    keyboard = [[InlineKeyboardButton("Sì", callback_data="yes"), InlineKeyboardButton("No", callback_data="no")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.callback_query.message.reply_text("Vuoi inserire altre eccezioni?", reply_markup=reply_markup)
    return MORE_EXCEPTIONS


async def handle_more_exceptions(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    if query.data == "yes":
        print("Gestisco altre eccezioni")
        return await ask_exception_day(update, context)
    else:
        print("Finisco la raccolta delle eccezioni")
        await query.answer()
        await query.message.reply_text("Grazie, la raccolta eccezioni è completa.")
        print("Mostro il riepilogo")
        logger.debug("Mostro il riepilogo")
        return await show_final_data(update, context)


# Funzione di mapping per il pattern settimanale
# Function to map weekly shifts to the required structure
def mappa_pattern_settimanale(pattern):
    giorni_settimana = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
    pattern_mappato = {}

    for index, giorno in enumerate(giorni_settimana):
        # Ottieni i turni per il giorno corrente dalla struttura fornita
        turni = pattern.get(giorno, [])

        # Se i turni non sono vuoti, formatta come richiesto
        if turni:
            pattern_mappato[index] = turni  # Keep the shifts as they are already formatted
        else:
            # Se non ci sono turni, assegna una lista vuota
            pattern_mappato[index] = []

    return pattern_mappato


# Funzione per mostrare il riepilogo dei dati raccolti
async def show_final_data(update: Update, context: CallbackContext) -> int:
    logger.info("Avvio della funzione mostra_riepilogo")

    riepilogo = "Riepilogo dei dati raccolti:\n\n"
    operatore = context.user_data.get('selected_worker', 'Non specificato')
    servizio = context.user_data.get('service', 'Non specificato')
    attivita = context.user_data.get('activity', 'Non specificato').split(":")[0].strip()
    utente_assistito = context.user_data.get('user_assisted', 'Non specificato')
    comune = context.user_data.get('selected_city', 'Non specificato')
    mese = context.user_data.get('selected_month_int', 'Non specificato')
    anno = context.user_data.get('selected_year_int', 'Non specificato')

    logger.info(f"Value: {context.user_data['selected_month_str']},"
                f"Value: {context.user_data['selected_year_str']},"
                f"Value: {context.user_data['selected_month_int']},"
                f"Value: {context.user_data['selected_year_int']}, ")

    # Raccogli i turni settimanali e le eccezioni
    weekly_shifts = context.user_data.get('weekly_shifts', {})
    work_exceptions = context.user_data.get('work_exceptions', {})

    # Prepara i dati per la tabella

    #Prepara il pattern settimanale nel formato corretto
    pattern_settimanale = mappa_pattern_settimanale(weekly_shifts)

    # Prepara le eccezioni nel formato corretto
    eccezioni = {}
    for giorno, dati in work_exceptions.items():
        # Assicurati che il giorno sia un intero
        giorno_numero = int(giorno)  # Converti la chiave in intero
        if isinstance(dati, list):
            # Se ci sono turni, ristruttura i dati
            turni = []
            codici_eccezione = []
            for turno in dati:
                if isinstance(turno, list):  # Se è un turno
                    turni.append(turno)  # Aggiungi il turno alla lista
                elif isinstance(turno, str):  # Se è un codice di eccezione
                    codici_eccezione.append(turno)  # Aggiungi il codice alla lista
            # Unisci turni e codici di eccezione
            eccezioni[giorno_numero] = turni + codici_eccezione  # Salva entrambi in una lista
        else:
            # Se è un codice di eccezione, mettilo in una lista
            eccezioni[giorno_numero] = [dati]  # Inserisci il codice in una lista

    # Stampa le eccezioni per verifica
    print(eccezioni)

    # Definisci il percorso del PDF da salvare
    output_path = f"giornaliera_{utente_assistito}.pdf"


    # Genera il PDF utilizzando i dati raccolti
    crea_tabella(output_path, mese, anno, pattern_settimanale, eccezioni, operatore, utente_assistito, comune,
                 attivita, servizio)

    # Verifica che il PDF sia stato creato
    if os.path.exists(output_path):
        # Invia il PDF all'utente
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(output_path, 'rb'))
        await update.callback_query.message.reply_text("PDF generato e inviato con successo.")
        # Send a sticker
        sticker_file_id = 'CAACAgIAAxkBAAIVrmcP-1Z2EaITHBC3F0hUUBBzqRztAAJIAgACVp29Chz1cvjcKRTQNgQ'
        await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker=sticker_file_id)
    else:
        await update.callback_query.message.reply_text("Errore durante la generazione del PDF.")

    return ConversationHandler.END


async def restart(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Riavvio della conversazione...")

    # Resetta i dati utente
    return await start(update, context)  # Ritorna allo stato iniziale


# Main function to set up the bot
def main() -> None:
    # Create the bot and define the handlers
    application = Application.builder().token("7883723109:AAFVf7e5Xaj-qORbjQ65SK4jTvvtvFJwXk8").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],  # Initial state is /start
        states={
            NAME: [CallbackQueryHandler(handle_worker_name)],  # Handle name selection with CallbackQueryHandler
            CITY: [CallbackQueryHandler(handle_city)],  # Handle city selection
            USER_ASSISTED: [CallbackQueryHandler(handle_user_assisted)],
            MONTH_AND_YEAR: [CallbackQueryHandler(handle_month_and_year)],  # Handle month selection
            SERVICE: [CallbackQueryHandler(handle_service)],
            ACTIVITY: [CallbackQueryHandler(handle_activity)],
            ASK_WORKDAY: [CallbackQueryHandler(handle_workday_response)],
            ADD_ANOTHER_SHIFT: [CallbackQueryHandler(handle_add_another_shift)],
            ASK_EXCEPTIONS: [CallbackQueryHandler(handle_work_exceptions)],
            SELECT_EXCEPTION_DAY: [CallbackQueryHandler(handle_exception_day)],
            WORKED_ON_EXCEPTION_DAY: [CallbackQueryHandler(handle_worked_on_exception_day)],
            EXCEPTIONS_SHIFT_START_HOUR: [CallbackQueryHandler(handle_exception_shift_start_hour)],
            EXCEPTIONS_SHIFT_START_MINUTE: [CallbackQueryHandler(handle_exception_shift_start_minute)],
            EXCEPTION_SHIFT_END_HOUR: [CallbackQueryHandler(handle_exception_shift_end_hour)],
            EXCEPTION_SHIFT_END_MINUTE: [CallbackQueryHandler(handle_exception_shift_end_minute)],
            EXCEPTION_CODE: [CallbackQueryHandler(handle_exception_code)],
            MORE_EXCEPTIONS: [CallbackQueryHandler(handle_more_exceptions)],
            ADD_ANOTHER_EXCEPTION_SHIFT: [CallbackQueryHandler(handle_add_another_exception_shift)],
            SHIFT_START_HOUR: [CallbackQueryHandler(handle_shift_start_hour)],  # Handle start hour selection
            SHIFT_START_MINUTE: [CallbackQueryHandler(handle_shift_start_minute)],  # Handle start minute selection
            SHIFT_END_HOUR: [CallbackQueryHandler(handle_shift_end_hour)],  # Handle end hour selection
            SHIFT_END_MINUTE: [CallbackQueryHandler(handle_shift_end_minute)],  # Handle end minute selection
        },
        fallbacks=[CommandHandler('restart', restart)]  # Add restart command
    )

    application.add_handler(conv_handler)
    application.add_handler(MessageHandler(filters.Sticker.ALL, sticker_handler))  # Gestisce tutti gli adesivi
    # Start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
