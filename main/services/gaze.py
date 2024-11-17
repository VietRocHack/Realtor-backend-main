from collections import Counter

FPS = 10
DURATION = 10
FRAME_COUNT = FPS * DURATION

def interpret_gaze_vector(vec):
    x, y, _ = map(float, vec)
    if -0.2 <= x <= 0.2 and -0.2 <= y <= 0.2:
        return 'ahead'
    elif x < 0 and y < 0:
        return 'left'
    elif x > 0 and y > 0:
        return 'right'
    elif x > 0 and y < 0:
        return 'up'
    elif x < 0 and y > 0:
        return 'down'
    else:
        return 'unknown'

def analyze_gaze_vectors(gaze_vectors):
    object_mapping = {
        'left': 'bottle',
        'right': 'laptop',
        'ahead': 'chair',
        'down': 'table',
        'up': 'ceiling'
    }
    
    frames_per_second = FPS
    
    results = []
    gaze_list = [gaze_vectors[str(i)] for i in range(FRAME_COUNT)]

    for i in range(DURATION):
        start_frame = i * frames_per_second
        end_frame = start_frame + frames_per_second
        second_vectors = gaze_list[start_frame:end_frame]
        
        interpreted_gazes = [interpret_gaze_vector(vec['vec']) for vec in second_vectors]
        direction_counts = Counter(interpreted_gazes)
        most_common_direction = direction_counts.most_common(1)[0][0]
        most_looked_object = object_mapping.get(most_common_direction, 'unknown')
        
        results.append(most_looked_object)
    
    return results