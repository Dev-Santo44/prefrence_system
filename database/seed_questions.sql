-- Seed survey questions for OCEAN personality traits (5 per trait = 25 questions)
USE preference_db;

INSERT INTO survey_questions (question_text, category) VALUES
-- Openness
('I enjoy exploring new ideas and concepts.', 'Openness'),
('I have a vivid imagination and enjoy creative thinking.', 'Openness'),
('I appreciate art, music, and literature.', 'Openness'),
('I enjoy learning about different cultures and perspectives.', 'Openness'),
('I prefer variety and novelty over routine.', 'Openness'),

-- Conscientiousness
('I always complete tasks on time and meet my deadlines.', 'Conscientiousness'),
('I keep my environment organized and tidy.', 'Conscientiousness'),
('I plan ahead before starting a new project.', 'Conscientiousness'),
('I pay close attention to details in my work.', 'Conscientiousness'),
('I follow through on my commitments and promises.', 'Conscientiousness'),

-- Extraversion
('I feel comfortable being the center of attention.', 'Extraversion'),
('I enjoy social gatherings and meeting new people.', 'Extraversion'),
('I tend to talk a lot and share my opinions freely.', 'Extraversion'),
('I get energized by spending time with others.', 'Extraversion'),
('I am often the one to start conversations.', 'Extraversion'),

-- Agreeableness
('I try to understand others'' feelings and emotions.', 'Agreeableness'),
('I enjoy helping others and cooperating in group tasks.', 'Agreeableness'),
('I avoid conflicts and prefer peaceful resolutions.', 'Agreeableness'),
('I trust people and assume they have good intentions.', 'Agreeableness'),
('I am compassionate and caring toward others.', 'Agreeableness'),

-- Neuroticism
('I often feel anxious or worried without a clear reason.', 'Neuroticism'),
('I get stressed easily when things do not go as planned.', 'Neuroticism'),
('I experience frequent mood swings.', 'Neuroticism'),
('I find it difficult to recover quickly from setbacks.', 'Neuroticism'),
('I tend to overthink and dwell on problems.', 'Neuroticism');
