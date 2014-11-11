class Observer(object):
    def __init__(self):
        self.subscribers = []

    #-----------------------------------------------------------------
    def subscribe(self, observer):
        """Add a subscriber.
        @param observer the object that will be observing

        This method adds subscribers to the list of observers for an
        observable object.
        """
        #---------------------------------------------------------
        # add observer if it is not in the list
        #---------------------------------------------------------
        if observer not in self.subscribers:
            self.subscribers.append(observer)
        else:
            raise ValueError("Observer is already registerd")

    #-----------------------------------------------------------------
    def unsubscribe(self, observer):
        """Remove a subscriber.
        @param observer - The observer object that needs to be removed

        This method removes the subscriber from the list of observers
        for an observable object.
        """
        #---------------------------------------------------------
        # assert if the observer is not in the observers list
        #---------------------------------------------------------
        if observer not in self.subscribers:
            raise ValueError("Observer is not registered")
        else:
            #-----------------------------------------------------
            # remove the observer
            #-----------------------------------------------------
            self.subscribers.remove(observer)

    #-----------------------------------------------------------------
    def signal_event(self, key):
        """Notify the observers with a given key.
        @param key - String of the notification type

        This method notifies the observers that have subscribed to get
        notifications of the given key.
        """
        #-------------------------------------------------------------
        # notify the observers by calling their update methods
        #-------------------------------------------------------------
        for subscriber in self.subscribers:
            subscriber.event_handler(key)
