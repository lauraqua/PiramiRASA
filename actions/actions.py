from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

info_descriptions = {
    "stanza": "Ti trovi in un'enorme stanza, praticamente vuota se non per una chiave a terra e una cassa. Verso sud vedi una porta.",
    "cassa": "Una semplice cassa chiusa da un lucchetto.",
    "chiave": "Una chiave luccicante si trova a terra al centro della stanza.",
    "porta": "Una porta decisamente datata e malridotta, ma non abbastanza per abbatterla a mano.",
    "biglietto": "Un biglietto con su scritto 'Lancia il mattone sulla porta'.",
    "mattone": "Un mattone."
}

OGGETTI_PRENDIBILI = ["chiave", "biglietto", "mattone"]

INTERAZIONI_SINGOLE = {
    "biglietto": "Leggi il biglietto: 'Lancia il mattone sulla porta'.",
    "cassa": "È chiusa da un robusto lucchetto. Ti serve qualcosa per aprirla.",
    "porta": "Provi a spingerla, ma non si muove di un millimetro."
}

INTERAZIONI_DOPPIE = {
    frozenset(["chiave", "cassa"]): "La chiave entra perfettamente nella serratura del lucchetto. La giri e la cassa si apre: all'interno trovi un biglietto e un mattone!",
    frozenset(["chiave", "porta"]): "La chiave è troppo piccola per l'ingombrante serratura della porta.",
    frozenset(["mattone", "porta"]): "Carichi con tutta la forza che hai e lanci il mattone contro la porta. Il legno cede e la porta si apre!"
}


class ActionInfo(Action):
    def name(self) -> Text:
        return "action_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        entities = tracker.latest_message.get("entities", [])
        spoken = False

        for blob in entities:
            if blob["entity"] in ["oggetto", "stanza"]:
                valore = blob["value"].lower().strip()
                if valore in info_descriptions:
                    dispatcher.utter_message(text=info_descriptions[valore])
                    spoken = True
                else:
                    dispatcher.utter_message(text=f"Non ho dettagli particolari su '{blob['value']}'.")
                    spoken = True

        if not spoken:
            inventario = tracker.get_slot("inventario") or []
            zaino = ", ".join(inventario) if inventario else "vuoto"
            descrizione_stanza = info_descriptions["stanza"]
            dispatcher.utter_message(text=f"{descrizione_stanza} \nZaino attuale: {zaino}")

        return []

class ActionPrendi(Action):
    def name(self) -> Text:
        return "action_prendi"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        inventario = list(tracker.get_slot("inventario") or [])
        entities = tracker.latest_message.get("entities", [])
        raccolto = False

        for blob in entities:
            if blob["entity"] == "oggetto":
                item = blob["value"].lower().strip()
                if item not in OGGETTI_PRENDIBILI:
                    dispatcher.utter_message(text=f"Non puoi prendere {item}.")
                    raccolto = True
                elif item in inventario:
                    dispatcher.utter_message(text=f"Hai già {item} nell'inventario.")
                    raccolto = True
                else:
                    inventario.append(item)
                    dispatcher.utter_message(text=f"Hai raccolto {item}, ora è nel tuo inventario.")
                    raccolto = True

        if raccolto:
            return [SlotSet("inventario", inventario)]

        dispatcher.utter_message(text="Sicuro di aver scritto correttamente l'oggetto da prendere?")
        return []
    
class ActionInteragisci(Action):
    def name(self) -> Text:
        return "action_interagisci"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        inventario = tracker.get_slot("inventario") or []
        entities = [
            e["value"].lower().strip()
            for e in tracker.latest_message.get("entities", [])
            if e["entity"] == "oggetto"
        ]

        for item in entities:
            if item in OGGETTI_PRENDIBILI and item not in inventario:
                dispatcher.utter_message(text=f"Non hai '{item}' nel tuo inventario.")
                return []

        if len(entities) == 1:
            item = entities[0]
            if item in INTERAZIONI_SINGOLE:
                dispatcher.utter_message(text=INTERAZIONI_SINGOLE[item])
            else:
                dispatcher.utter_message(text=f"Non puoi interagire direttamente con '{item}'.")
            return []

        if len(entities) == 2:
            coppia = frozenset(entities)
            if coppia in INTERAZIONI_DOPPIE:
                dispatcher.utter_message(text=INTERAZIONI_DOPPIE[coppia])
            else:
                dispatcher.utter_message(text=f"'{entities[0]}' e '{entities[1]}' non possono essere combinati assieme.")
            return []

        dispatcher.utter_message(text="Non ho capito con quali oggetti vuoi interagire, riprova.")
        return []
                        