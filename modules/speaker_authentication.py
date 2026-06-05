from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import logging

class SpeakerAuthenticator:
    def __init__(self, similarity_threshold=0.65, min_delta=0.02):
        self.encoder = VoiceEncoder()
        self.similarity_threshold = similarity_threshold
        self.min_delta = min_delta
        logging.info(f"Speaker Authenticator initialized with threshold: {self.similarity_threshold} and delta: {self.min_delta}")

    def extract_embedding(self, audio_data):
        """
        Extracts embedding from audio data.
        :param audio_data: numpy array of audio samples or path to wav file
        :return: embedding vector or None if failed
        """
        try:
            # If audio_data is a path, preprocess it. If it's already a numpy array, use it directly.
            if isinstance(audio_data, str):
                wav = preprocess_wav(audio_data)
            else:
                wav = audio_data
            
            embedding = self.encoder.embed_utterance(wav)
            return embedding
        except Exception as e:
            logging.error(f"Error extracting embedding: {e}")
            return None

    def verify(self, target_embedding, stored_profiles):
        """
        Verifies the speaker against stored profiles.
        :param target_embedding: The embedding of the current speaker
        :param stored_profiles: Dictionary of {username: embedding}
        :return: Dict with authentication result
        """
        best_score = -1.0
        second_best_score = -1.0
        best_match_user = None

        if target_embedding is None:
             return {
                "authenticated": False,
                "username": None,
                "confidence": 0.0,
                "message": "Invalid input embedding"
            }

        if not stored_profiles:
             return {
                "authenticated": False,
                "username": None,
                "confidence": 0.0,
                "message": "No registered users"
            }

        for username, profile_embedding in stored_profiles.items():
            if profile_embedding is None:
                continue
                
            # Cosine similarity
            score = np.dot(target_embedding, profile_embedding) / (
                np.linalg.norm(target_embedding) * np.linalg.norm(profile_embedding)
            )
            
            if score > best_score:
                second_best_score = best_score
                best_score = score
                best_match_user = username
            elif score > second_best_score:
                second_best_score = score

        logging.info(f"Best match: {best_match_user} with score: {best_score} (Threshold: {self.similarity_threshold})")
        
        authenticated = False
        low_confidence = False
        message = ""
        
        if best_score >= self.similarity_threshold:
            authenticated = True
            message = "Authentication successful"
        elif best_score >= (self.similarity_threshold - 0.05):
            authenticated = True
            low_confidence = True
            message = "Authentication successful (low confidence)"
            logging.info(f"Score: {best_score:.2f} (near threshold)")
        else:
            message = "Authentication failed"
        
        # Identity disambiguation check if there are multiple users
        if authenticated and len(stored_profiles) > 1:
            delta = best_score - second_best_score
            if delta < self.min_delta:
                authenticated = False
                message = f"Ambiguous voice. Too close to another user (Delta: {delta:.3f} < {self.min_delta})"
                logging.warning(message)
            else:
                logging.info(f"Voice clearly distinguished (Delta: {delta:.3f} >= {self.min_delta})")
            
        result = {
            "authenticated": authenticated,
            "username": best_match_user if authenticated else None,
            "confidence": float(best_score),
            "low_confidence": low_confidence,
            "message": message
        }
        
        logging.info(f"Verification Check: {result}")
        return result

    def verify_embedding(self, embedding1, embedding2):
        """
        Calculates cosine similarity between two embeddings.
        :param embedding1: numpy array
        :param embedding2: numpy array
        :return: similarity score (float)
        """
        if embedding1 is None or embedding2 is None:
            return 0.0
            
        score = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return float(score)
