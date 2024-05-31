import openai
from dotenv import load_dotenv
import os
import argparse
import spotipy
import json

load_dotenv()

if "OPENAI_API_KEY" not in os.environ:
  raise ValueError("OPENAI_API_KEY is missing from the .env file, please provide one.")
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Create a Playlist with OpenAI
def get_playlist(input_text, count=8, model="gpt-3.5-turbo"):
    system_prompt = """
    You are a helpful playlist generating assistant. You should generate a list of songs and their artists according to a text prompt.
    You should return a JSON array only, where each element follows this format: {"song": "<song_title>", "artist": "<artist>"}
    Use double quotes for the keys and values. Do not include any other information in the JSON array.
    """
    user_prompt1 = "Generate a playlist of 4 songs based on this prompt: super sad songs"
    assistant_answer = [{"song": "Hurt", "artist": "Johnny Cash"},{"song": "The Scientist", "artist": "Coldplay"},{"song": "Everybody Hurts", "artist": "R.E.M."},{"song": "Tears in Heaven", "artist": "Eric Clapton"}]
    
    user_prompt2 = f"Generate a playlist of {count} songs based on this prompt: {input_text}"
    
    response = openai.chat.completions.create(
        model=model,
        messages=[
            {
              "role": "system",
              "content": f"{system_prompt}"
            },
            {
              "role": "user",
              "content": f"{user_prompt1}"
            },
            {
              "role": "assistant",
              "content": f"{assistant_answer}"
            },
            {
              "role": "user",
              "content": f"{user_prompt2}"
            }
        ])
    
    playlist = json.loads(response.choices[0].message.content)

    return playlist


def connect_to_spotify():
  sp = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
      client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
      client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
      redirect_uri="http://localhost:9999",
      scope="playlist-modify-private"
    )
  )

  current_user = sp.current_user()
  return sp, current_user


def main():
  # Parse the command line arguments
  parser = argparse.ArgumentParser(description="Simple command line playlist generator using OpenAI and Spotify.")
  parser.add_argument("-p", type=str, default="OpenAI songs", help="The prompt to describe the playlist")
  parser.add_argument("-n", type=str, default="8", help="The number of songs to generate")
  parser.add_argument("-m", type=str, default="gpt-3.5-turbo", help="The OpenAI model to use")
  args = parser.parse_args()

  # Create a list of tracks wit OpenAI
  playlist = get_playlist(args.p, args.n, args.m)

  # Connect to Spotify
  sp, current_user = connect_to_spotify()
  assert current_user is not None, "Failed to authenticate with Spotify"

  # Extract the track IDs from the playlist
  track_ids = []
  for item in playlist:
      print(item)
      artist, song = item["artist"], item["song"]
      query = f"{song} by {artist}"
      search_resuts = sp.search(q=query, limit=1, type="track")
      track_id = search_resuts["tracks"]["items"][0]["id"]
      track_ids.append(track_id)

  # Create a new playlist on Spotify
  created_playlist = sp.user_playlist_create(
    current_user["id"],
    public=False,
    name=f"{args.p}",
  )

  # Add the tracks to the playlist
  sp.user_playlist_add_tracks(
    current_user["id"],
    created_playlist["id"],
    track_ids
  )

if __name__ == "__main__":
  main()