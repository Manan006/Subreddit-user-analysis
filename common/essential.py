import sys
import dotenv

class essentials: # Is considered essential for the bot to run
    def __init__(self, loop=None):
        self.loop = loop
        self.get_essentials()
        self.do_essentials()

    def get_essentials(self):
        self.sys = sys
        try:
            if self.loop != None:
                import nest_asyncio
                self.nest_asyncio = nest_asyncio
            self.dotenv = dotenv
        except ImportError:
            print("Failed to import dependencies : essentials")
            sys.exit(1)

    def do_essentials(self):
        try:
            self.dotenv.load_dotenv() # Load the .env file
            if self.loop != None:
                self.nest_asyncio.apply(self.loop) # Apply nest_asyncio patch to the loop
        except Exception as e:
            print(e)
            print("Failed to do essentials")
            self.sys.exit(1)
