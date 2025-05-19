
class NotesProvider:
    def __init__(self, event_provider):
        self.event_provider = event_provider

    def get_notes_markdown(self):
        # TODO: replace with actual notes/events markdown
        return (
            "## Notes&Events\n\n"
            "Regem aderam Romani Achivis raucos \n"
            "1. Pudore ars aeternum temperie\n"
            "2. Inroravere nunc leones et quam pactaque illa\n"
            "3. Neve ac pro temerare dant"
        )
