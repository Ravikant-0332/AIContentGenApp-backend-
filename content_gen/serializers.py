from rest_framework import serializers

class PromptSerializer(serializers.Serializer):
    process_name = serializers.CharField(max_length=100)

class GptResponseSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    difficulty = serializers.CharField()
    question_type = serializers.CharField()
    topic = serializers.CharField()
    subtopic = serializers.CharField()
    number_of_question = serializers.IntegerField()
    is_updated = serializers.BooleanField(required=False)
    process_name = serializers.CharField(max_length=100, required=False)

class ContextSerializer(serializers.Serializer):
    context = serializers.CharField()
    difficulty = serializers.ChoiceField(choices=['EASY', 'MEDIUM', 'HARD', 'easy', 'medium', 'hard'])
    subtopic = serializers.CharField()

class CodingCuratorSerializer(serializers.Serializer):
    contexts = ContextSerializer(many=True)


