import requests
import time
import random





from youtube_transcript_api import YouTubeTranscriptApi
import requests
import random
import re  # Import the regular expression module






def extract_transcript_details(video_id):
    """
    Extracts transcript details from a YouTube video, using a rotating proxy to avoid IP blocking.

    Args:
        video_id (str): The YouTube video ID.

    Returns:
        str: The full transcript text, or None if no transcript is found or an error occurs.
    """

    # Webshare proxy configuration (Add more proxies to this list for better rotation)
    proxy_list = [
        "http://uvmfwcbs-rotate:imui7uhheoxm@p.webshare.io:80",
        # "http://user2:pass2@host2:port2",  # Add more proxies here to rotate through
        # "http://user3:pass3@host3:port3",
    ]

    



    def get_working_proxy(proxies):
        """
        Checks if the proxies are working and returns a working proxy.
        Args:
            proxies (list): A list of proxy URLs
        Returns:
             str: A working proxy.
        """
        for proxy_url in proxies:
            try:
                print(f"ℹ️  Checking proxy: {proxy_url}")
                response = requests.get(
                    "https://ipv4.webshare.io/",
                    proxies={"http": proxy_url, "https": proxy_url},
                    timeout=5  # Added timeout
                )
                response.raise_for_status()
                response_text = response.text

                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", response_text):
                    print(f"✅  Working proxy: {proxy_url}, IP: {response_text}")
                    return proxy_url
                else:
                    print(
                        f"❌  Proxy {proxy_url} did not return an IP address.  Response: {response_text}"
                    )

            except requests.exceptions.RequestException as e:
                print(f"❌  Proxy {proxy_url} failed: {e}")
        return None

    original_get = requests.get  # Store the original requests.get

    try:
        working_proxy = get_working_proxy(proxy_list)
        if not working_proxy:
            raise Exception("No working proxies available")

        def proxy_get(*args, **kwargs):
            kwargs["proxies"] = {"http": working_proxy, "https": working_proxy}
            return original_get(*args, **kwargs)

        requests.get = proxy_get  # Apply the monkey patch

        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        available_languages = [t.language_code for t in transcripts]
        print(f"Available transcripts for video {video_id}: {available_languages}")

        for lang in ["en", "en-IN", "hi"]:
            if lang in available_languages:
                try:
                    transcript = transcripts.find_transcript([lang])
                    transcript_data = transcript.fetch()
                    full_transcript = " ".join([item.text for item in transcript_data])
                    print(f"✅ Retrieved transcript for {lang}")
                    return full_transcript
                except Exception as e:
                    print(f"❌ Error retrieving transcript for {lang}: {e}")
        raise ValueError(
            f"No transcripts found in preferred languages. Available: {available_languages}"
        )

    except Exception as e:
        print(f"❌ Error during transcript extraction: {e}")
        return None  # Important:  Return None on error, don't just raise.
    finally:
        requests.get = original_get  # Restore the original requests.get


if __name__ == "__main__":
    # Example Usage
    video_id_to_test = "HISRUrJsD08"  # Replace with a YouTube video ID.
    transcript = extract_transcript_details(video_id_to_test)
    if transcript:
        print(transcript)
    else:
        print("Failed to retrieve transcript.")



