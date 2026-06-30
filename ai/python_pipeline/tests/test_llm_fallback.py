import os
import unittest
from unittest.mock import MagicMock, patch
from ai.python_pipeline.llm_client import LLMClient

class TestLLMFallback(unittest.TestCase):
    def test_gemini_fallback_to_groq(self):
        # Setup mock env keys
        with patch.dict(os.environ, {
            'LLM_PROVIDER': 'gemini',
            'GROQ_API_KEY': 'test-groq-key',
            'GROQ_MODEL': 'llama-3.3-70b-versatile'
        }):
            # Create LLMClient
            client = LLMClient()
            
            # Mock self._client.models.generate_content to raise an exception (simulate Gemini failure)
            client._client = MagicMock()
            client._client_name = 'genai'
            client._client.models.generate_content.side_effect = Exception("Gemini service unavailable")

            # Mock requests.post to simulate Groq API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [
                    {
                        'message': {
                            'content': 'Response from Groq'
                        }
                    }
                ]
            }

            with patch('requests.post', return_value=mock_response) as mock_post:
                result = client.complete("Hello, this is a test prompt")
                
                # Verify Groq was called
                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                assert kwargs['headers']['Authorization'] == 'Bearer test-groq-key'
                assert kwargs['json']['model'] == 'llama-3.3-70b-versatile'
                assert kwargs['json']['messages'] == [{'role': 'user', 'content': 'Hello, this is a test prompt'}]

                # Verify result contains the Groq response
                self.assertEqual(result['text'], 'Response from Groq')
                self.assertEqual(result['raw'], mock_response.json.return_value)

    def test_think_tag_stripping(self):
        # Create LLMClient
        client = LLMClient()
        
        # Mock self._client.models.generate_content to return a thinking block and JSON response
        client._client = MagicMock()
        client._client_name = 'genai'
        
        mock_resp = MagicMock()
        mock_resp.text = "<think>\nThinking about the story...\n</think>\n{\"title\": \"カフェでの出会い\"}"
        client._client.models.generate_content.return_value = mock_resp

        # Setup env key
        with patch.dict(os.environ, {'LLM_PROVIDER': 'gemini'}):
            result = client.complete("Hello")
            self.assertEqual(result['text'], '{"title": "カフェでの出会い"}')

if __name__ == '__main__':
    unittest.main()
