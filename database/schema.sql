-- Table users
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user'
);

-- Table survey_questions
CREATE TABLE survey_questions (
    q_id INT AUTO_INCREMENT PRIMARY KEY,
    question_text TEXT NOT NULL,
    category ENUM('Openness', 'Conscientiousness', 'Extraversion', 'Agreeableness', 'Neuroticism') NOT NULL
);

-- Table responses
CREATE TABLE responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    q_id INT,
    answer VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (q_id) REFERENCES survey_questions(q_id)
);

-- Table preference_results
CREATE TABLE preference_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    openness_score FLOAT,
    conscientiousness_score FLOAT,
    extraversion_score FLOAT,
    agreeableness_score FLOAT,
    neuroticism_score FLOAT,
    recommendations TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
