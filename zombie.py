from pico2d import *

import random
import math
import game_framework
import game_world
from behavior_tree import BehaviorTree, Action, Sequence, Condition, Selector
import play_mode


# zombie Run Speed
PIXEL_PER_METER = (10.0 / 0.3)  # 10 pixel 30 cm
RUN_SPEED_KMPH = 10.0  # Km / Hour
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM / 60.0)
RUN_SPEED_PPS = (RUN_SPEED_MPS * PIXEL_PER_METER)

# zombie Action Speed
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 10.0

animation_names = ['Walk', 'Idle']


class Zombie:
    images = None

    def load_images(self):
        if Zombie.images == None:
            Zombie.images = {}
            for name in animation_names:
                Zombie.images[name] = [load_image("./zombie/" + name + " (%d)" % i + ".png") for i in range(1, 11)]
            Zombie.font = load_font('ENCR10B.TTF', 40)
            Zombie.marker_image = load_image('hand_arrow.png')


    def __init__(self, x=None, y=None):
        self.x = x if x else random.randint(100, 1180)
        self.y = y if y else random.randint(100, 924)
        self.load_images()
        self.dir = 0.0      # radian 값으로 방향을 표시
        self.speed = 0.0
        self.frame = random.randint(0, 9)
        self.state = 'Idle'
        self.ball_count = 0

        self.tx, self.ty = 1000,1000
        self.build_behavior_tree()
        self.patrol_locations = [
            (43,274), (1110,274), (1050,494), (575,804),(235,991),(575,804),(1050,494)
        ]
        self.loc_no =0
    def get_bb(self):
        return self.x - 50, self.y - 50, self.x + 50, self.y + 50


    def update(self):
        self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % FRAMES_PER_ACTION
        # fill here
        self.bt.run()

    def draw(self):
        if math.cos(self.dir) < 0:
            Zombie.images[self.state][int(self.frame)].composite_draw(0, 'h', self.x, self.y, 100, 100)
        else:
            Zombie.images[self.state][int(self.frame)].draw(self.x, self.y, 100, 100)
        self.font.draw(self.x - 10, self.y + 60, f'{self.ball_count}', (0, 0, 255))
        Zombie.marker_image.draw(self.tx + 25, self.ty - 25)
        draw_rectangle(*self.get_bb())

    def handle_event(self, event):
        pass

    def handle_collision(self, group, other):
        if group == 'zombie:ball':
            self.ball_count += 1


    def set_target_location(self, x=None, y=None):
        if not x or not y:
            raise ValueError('위치지정해야함')
        self.tx,self.ty = x,y
        return BehaviorTree.SUCCESS


    def distance_less_than(self, x1, y1, x2, y2, r):
        distance2 = (x1-x2)**2+(y1-y2)**2
        return distance2< (r*PIXEL_PER_METER)**2
        pass
    def distance_more_than(self, x1, y1, x2, y2, r):
        distance2 = (x1-x2)**2+(y1-y2)**2
        return distance2> (r*PIXEL_PER_METER)**2
        pass
    def move_slightly_to(self, tx, ty):
        self.dir = math.atan2(ty-self.y, tx-self.x)
        self.speed = RUN_SPEED_PPS
        self.x += self.speed * math.cos(self.dir)*game_framework.frame_time
        self.y += self.speed * math.sin(self.dir) * game_framework.frame_time
        pass

    def move_to(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(self.tx,self.ty)
        if self.distance_less_than(self.tx,self.ty,self.x,self.y,r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING
        pass

    def set_random_location(self):
        self.tx,self.ty = random.randint(100,1280-100),random.randint(100,1240-100)
        pass

    def is_boy_nearby(self, r):
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y,r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL
        pass

    def ball_count_avoid(self):
        if self.ball_count < play_mode.boy.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL
        pass

    def ball_count_chase(self):
        if self.ball_count >= play_mode.boy.ball_count:
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.FAIL
        pass

    def move_to_boy(self, r=0.5):
        self.state = 'Walk'
        self.move_slightly_to(play_mode.boy.x, play_mode.boy.y)
        if self.distance_less_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING
        pass

    def get_patrol_location(self):
        self.tx, self.ty = self.patrol_locations[self.loc_no]
        self.loc_no = (self.loc_no+1)% len(self.patrol_locations)
        return BehaviorTree.SUCCESS
        pass

    def avoid_to_boy(self, r=0.5):
        self.state = 'Avoid'
        self.move_slightly_to(play_mode.boy.x, play_mode.boy.y)
        if self.distance_more_than(play_mode.boy.x, play_mode.boy.y, self.x, self.y, r):
            return BehaviorTree.SUCCESS
        else:
            return BehaviorTree.RUNNING
        pass
    def build_behavior_tree(self):



        c2 = Condition('ball_count_avoid', self.ball_count_avoid)
        c3 = Condition('ball_count_chase', self.ball_count_chase)
        a4 = Action('Move to boy', self.move_to_boy)
        SEQ_chase_boy = Sequence('Chase boy', c3, a4)
        a6 = Action('Avoid', self.avoid_to_boy)
        SEQ_avoid_boy = Sequence('Avoid boy', c2, a6)
        SEL_avoid_or_chase = Selector('Chose one', SEQ_chase_boy,SEQ_avoid_boy)

        c1 = Condition('Near boy', self.is_boy_nearby, 7)
        SEQ_avoid_or_chase = Sequence('avoid or chase', c1, SEL_avoid_or_chase )


        a2 = Action('Move to', self.move_to)  # action node생
        a5 = Action('Take Patrol location', self.get_patrol_location)
        SEQ_patrol = Sequence('Patrol', a5, a2)
        root = SEL_chase_or_patrol = Selector('Chase or patrol', SEQ_avoid_or_chase, SEQ_patrol)

        self.bt = BehaviorTree(root)
        pass
