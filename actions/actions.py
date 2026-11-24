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

ABLE_TO_PICK_UP = ["chiave", "biglietto", "mattone"]


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
            dispatcher.utter_message(text=f"Cosa vuoi osservare nel dettaglio? (Zaino attuale: {zaino})")

        return []


class ActionPrendi(Action):
    def name(self) -> Text:
        return "action_prendi"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        inventario = list(tracker.get_slot("inventario") or [])
        raccolto = False

        for blob in tracker.latest_message.get("entities", []):
            if blob["entity"] == "oggetto":
                item = blob["value"].lower().strip()
                if item not in ABLE_TO_PICK_UP:
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