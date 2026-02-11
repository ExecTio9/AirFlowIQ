# this handles all the data fetching from supa base to keep the UI responsive
# this runs all the queries in a separate thread in the background, so the UI
# keeps active in the foreground (what the users see)
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal
from supabase import create_client

from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE

# create a supabase loader instance
class SupabaseDataLoader(QThread):

    #signals being emitted by thread
    dataFetched = pyqtSignal(pd.DataFrame)
    averagesFetched = pyqtSignal(dict)
    devicesFetched = pyqtSignal(list)
    errorOccurred = pyqtSignal(str) #emits the error message string

    #different fetch modes for what we're fetching to display in the UI
    # example: loader = SupabaseDataLoader(SupabaseDataLoader.FETCH_MODE_GRAPH)
    FETCH_MODE_GRAPH = 1
    FETCH_MODE_AVERAGES = 2
    FETCH_MODE_DEVICES = 3

    # this is the constructor. basically initializes the class
    def __init__(self, mode, device_id=None, user_session=None, time_range_hours=None, parent=None):
        super().__init__(parent) #parent constructor is always called first
        self.mode = mode
        self.device_id = device_id
        self.user_session = user_session
        self.time_range_hours = time_range_hours  # Filter by time range (in hours)

    # this runs in the background of the UI. all data is fetched here
    # when complete, it will emit a signal with the data
    # do not touch UI elements from this thread
    # try to handle ALL exceptions
    def run(self):
        # try/except wrapper catches all the errors
        try:
            # creating a new client each time for thread safety
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY) #handles communication between app and supabase

            # Set user auth session
            if self.user_session:
                supabase.auth.set_session(
                    access_token=self.user_session.access_token, #short-lived token
                    refresh_token=self.user_session.refresh_token #long-lived token
                )
            ##### MODE 1 #####
            if self.mode == self.FETCH_MODE_GRAPH:
                #querying the database
                query = supabase.table(SUPABASE_TABLE).select("*")
                # ^ this is the format of the query. will select one table and all columns

                # filtering by device selected on graph
                if self.device_id:
                    # security check
                    if self.user_session and self.user_session.user:
                        user_id = self.user_session.user.id
                        #verifying ownership again with a query
                        #SQL equivalent: SELECT id FROM devices WHERE id = 'device_id' AND owner_id = 'user_id'
                        device_check = supabase.table("devices") \
                            .select("id") \
                            .eq("id", self.device_id) \
                            .eq("owner_id", user_id) \
                            .execute()

                        #if they do not have access or the device foes not exist, then exit
                        if not device_check.data:
                            self.errorOccurred.emit("Access denied: Device does not belong to you")
                            return

                    # now that ownership is verified, filter to this device
                    query = query.eq("device_id", self.device_id)

                    # "All my Devices" is selected on the graph
                else:
                    if self.user_session and self.user_session.user:
                        user_id = self.user_session.user.id

                        # a query to get the list of ALL devices owned by the user
                        # SQL: SELECT id FROM devices WHERE owner_id = 'user_id'
                        user_devices = supabase.table("devices") \
                            .select("id") \
                            .eq("owner_id", user_id) \
                            .execute()

                        # case if user has no devices at all
                        if not user_devices.data:
                            self.errorOccurred.emit("No devices found for this user")
                            return

                        # this extracts the device IDs into a list of strings
                        device_ids = [d["id"] for d in user_devices.data]

                        # filter query to only get data from these devices IDs
                        # SQL: SELECT * FROM sensor_logs WHERE device_id IN ('device1', 'device2', ...)
                        query = query.in_("device_id", device_ids)

                # IMPROVED TIME FILTERING LOGIC
                # Two-step filtering: Data will always be the most recently recorded, even if it is old data
                # Data displayed on the graph will
                # add warning if data is fall back
                if self.time_range_hours:
                    from datetime import datetime, timedelta, timezone

                    #calculating cut off time by subtraction
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.time_range_hours)
                    cutoff_str = cutoff_time.isoformat()

                    # Build query with time filter
                    # gte = "greater than or equal"
                    # gets all sensor data past a specified time
                    time_filtered_query = query.gte("recorded_at", cutoff_str).order("recorded_at", desc=False)
                    response = time_filtered_query.execute()

                    # Step 2: fallback to last recorded data in the timeframe
                    if not response.data or len(response.data) == 0:
                        # add warning here

                        print(f"\n⚠️  No data in the last {self.time_range_hours} hours")
                        print(f"   Falling back to: Most recent {self.time_range_hours} hours of available data")

                        # Rebuild query to get most recent timestamp
                        # We need to apply the same device filters
                        # can't call select twice on the same query because it causes an error
                        max_query = supabase.table(SUPABASE_TABLE).select("recorded_at")

                        # Apply same device filtering as before
                        if self.device_id:
                            max_query = max_query.eq("device_id", self.device_id)
                        else:
                            if self.user_session and self.user_session.user:
                                user_id = self.user_session.user.id
                                user_devices = supabase.table("devices") \
                                    .select("id") \
                                    .eq("owner_id", user_id) \
                                    .execute()
                                if user_devices.data:
                                    device_ids = [d["id"] for d in user_devices.data]
                                    max_query = max_query.in_("device_id", device_ids)

                        # gets the most recently recorded timestamps
                        max_query = max_query.order("recorded_at", desc=True).limit(1)
                        max_response = max_query.execute()

                        if not max_response.data or len(max_response.data) == 0:
                            print(f"   ❌ No data found at all for this device/user")
                            self.dataFetched.emit(pd.DataFrame())
                            return

                        # Get the most recent timestamp
                        most_recent_str = max_response.data[0]['recorded_at']
                        most_recent = pd.to_datetime(most_recent_str, utc=True)

                        # Calculate new cutoff: most_recent - time_range_hours
                        new_cutoff = most_recent - timedelta(hours=self.time_range_hours)
                        new_cutoff_str = new_cutoff.isoformat()

                        print(f"   📊 Most recent data: {most_recent_str}")
                        print(f"   📊 Showing data from: {new_cutoff_str} to {most_recent_str}")
                        print(f"   📊 (This is the most recent {self.time_range_hours} hours of available data)\n")

                        # Rebuild the full query with new cutoff
                        fallback_query = supabase.table(SUPABASE_TABLE).select("*")

                        # Apply same device filtering
                        if self.device_id:
                            fallback_query = fallback_query.eq("device_id", self.device_id)
                        else:
                            if self.user_session and self.user_session.user:
                                user_id = self.user_session.user.id
                                user_devices_data = supabase.table("devices") \
                                    .select("id") \
                                    .eq("owner_id", user_id) \
                                    .execute()
                                if user_devices_data.data:
                                    device_ids = [d["id"] for d in user_devices_data.data]
                                    fallback_query = fallback_query.in_("device_id", device_ids)

                        # Apply time filter and order
                        fallback_query = fallback_query.gte("recorded_at", new_cutoff_str).order("recorded_at",
                                                                                                 desc=False)
                        response = fallback_query.execute()

                        if not response.data or len(response.data) == 0:
                            print(f"   ❌ Still no data found (this shouldn't happen)")
                            self.dataFetched.emit(pd.DataFrame())
                            return
                    else:
                        print(
                            f"✅ Found {len(response.data)} rows in last {self.time_range_hours} hours (current time window)")

                else:
                    # No time filter - get all data
                    query = query.order("recorded_at", desc=False)
                    response = query.execute()

                    if not response.data or len(response.data) == 0:
                        print(f"No data found")
                        self.dataFetched.emit(pd.DataFrame())
                        return

                #responde.data is a list of dictionaries.
                # pd.DataFrame converts this to a table structure with rows and columns
                df = pd.DataFrame(response.data)

                # convert the recorded_at strings to datetime obejcts
                if "recorded_at" in df.columns:
                    df["recorded_at"] = pd.to_datetime(df["recorded_at"], utc=True)

                print(f"📈 Returning {len(df)} rows to display")
                if len(df) > 0:
                    min_time = df["recorded_at"].min()
                    max_time = df["recorded_at"].max()
                    print(f"   Time range: {min_time} to {max_time}")

                # emitting the signal with the dataframe safely passes it to the main thread
                # now we can connect any slot function to the signal in the UI file
                self.dataFetched.emit(df)

            #SECOND FETCH MODE
            elif self.mode == self.FETCH_MODE_AVERAGES:
                #logic is mostly the same as first fetch mode
                query = supabase.table(SUPABASE_TABLE).select("*")

                # Build device filter
                if self.device_id:
                    if self.user_session and self.user_session.user:
                        user_id = self.user_session.user.id

                        device_check = supabase.table("devices") \
                            .select("id") \
                            .eq("id", self.device_id) \
                            .eq("owner_id", user_id) \
                            .execute()

                        if not device_check.data:
                            self.errorOccurred.emit("Access denied: Device does not belong to you")
                            return

                    query = query.eq("device_id", self.device_id)
                else:
                    if self.user_session and self.user_session.user:
                        user_id = self.user_session.user.id

                        user_devices = supabase.table("devices") \
                            .select("id") \
                            .eq("owner_id", user_id) \
                            .execute()

                        if not user_devices.data:
                            self.errorOccurred.emit("No devices found for this user")
                            return

                        device_ids = [d["id"] for d in user_devices.data]
                        query = query.in_("device_id", device_ids)

                # ✨ IMPROVED TIME FILTERING FOR AVERAGES (same logic)
                if self.time_range_hours:
                    from datetime import datetime, timedelta, timezone

                    # Try standard time window first
                    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.time_range_hours)
                    cutoff_str = cutoff_time.isoformat()

                    time_filtered_query = query.gte("recorded_at", cutoff_str)
                    response = time_filtered_query.execute()

                    # Fall back to most recent X hours if no data in current window
                    if not response.data or len(response.data) == 0:
                        print(f"   Averages: No data in last {self.time_range_hours} hours, using most recent data")

                        # Rebuild query to get most recent timestamp
                        max_query = supabase.table(SUPABASE_TABLE).select("recorded_at")

                        # Apply same device filtering
                        if self.device_id:
                            max_query = max_query.eq("device_id", self.device_id)
                        else:
                            if self.user_session and self.user_session.user:
                                user_id = self.user_session.user.id
                                user_devices = supabase.table("devices") \
                                    .select("id") \
                                    .eq("owner_id", user_id) \
                                    .execute()
                                if user_devices.data:
                                    device_ids = [d["id"] for d in user_devices.data]
                                    max_query = max_query.in_("device_id", device_ids)

                        max_query = max_query.order("recorded_at", desc=True).limit(1)
                        max_response = max_query.execute()

                        if not max_response.data or len(max_response.data) == 0:
                            # No data at all
                            averages = {
                                "temp": None,
                                "humidity": None,
                                "pressure": None,
                                "windspeed": None,
                                "rfid": "N/A"
                            }
                            self.averagesFetched.emit(averages)
                            return

                        # Calculate fallback cutoff
                        most_recent_str = max_response.data[0]['recorded_at']
                        most_recent = pd.to_datetime(most_recent_str, utc=True)
                        new_cutoff = most_recent - timedelta(hours=self.time_range_hours)
                        new_cutoff_str = new_cutoff.isoformat()

                        # Rebuild query with new cutoff
                        fallback_query = supabase.table(SUPABASE_TABLE).select("*")

                        # Apply same device filtering
                        if self.device_id:
                            fallback_query = fallback_query.eq("device_id", self.device_id)
                        else:
                            if self.user_session and self.user_session.user:
                                user_id = self.user_session.user.id
                                user_devices_data = supabase.table("devices") \
                                    .select("id") \
                                    .eq("owner_id", user_id) \
                                    .execute()
                                if user_devices_data.data:
                                    device_ids = [d["id"] for d in user_devices_data.data]
                                    fallback_query = fallback_query.in_("device_id", device_ids)

                        # Apply time filter
                        fallback_query = fallback_query.gte("recorded_at", new_cutoff_str)
                        response = fallback_query.execute()

                        if not response.data or len(response.data) == 0:
                            averages = {
                                "temp": None,
                                "humidity": None,
                                "pressure": None,
                                "windspeed": None,
                                "rfid": "N/A"
                            }
                            self.averagesFetched.emit(averages)
                            return
                else:
                    # No time filter
                    response = query.execute()

                    if not response.data or len(response.data) == 0:
                        averages = {
                            "temp": None,
                            "humidity": None,
                            "pressure": None,
                            "windspeed": None,
                            "rfid": "N/A"
                        }
                        self.averagesFetched.emit(averages)
                        return

                # Calculate averages
                # convert to data frame again
                df = pd.DataFrame(response.data)
                # noge rfid returns last recorded value since it does not need an average
                averages = {
                    "temp": df["temp_c"].mean() if "temp_c" in df and len(df) > 0 else None,
                    "humidity": df["humidity"].mean() if "humidity" in df and len(df) > 0 else None,
                    "pressure": df["pressure_pa"].mean() if "pressure_pa" in df and len(df) > 0 else None,
                    "windspeed": df["windSpeed"].mean() if "windSpeed" in df and len(df) > 0 else None,
                    "rfid": df["rfid"].iloc[-1] if "rfid" in df and not df.empty else "N/A"
                }

                self.averagesFetched.emit(averages)

            # fetches the list if devices for the devices tab
            elif self.mode == self.FETCH_MODE_DEVICES:
                if self.user_session and self.user_session.user:
                    user_id = self.user_session.user.id

                    response = supabase.table("devices") \
                        .select("id, name, hvac_location, created_at, owner_id") \
                        .eq("owner_id", str(user_id)) \
                        .execute()

                    if response.data:
                        print(f"Found {len(response.data)} devices for user")
                        self.devicesFetched.emit(response.data)
                    else:
                        self.devicesFetched.emit([])
                else:
                    self.errorOccurred.emit("Not authenticated")

        except Exception as e:
            print(f"Error in SupabaseDataLoader: {e}")
            self.errorOccurred.emit(str(e))