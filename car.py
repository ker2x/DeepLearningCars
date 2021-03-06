import math
import numpy as np
import random

from physic import PhysicsEntity
from primitives import *


def logistic(r, x):
    return r * x * (1 - x)


def logi(r):
    x = .6
    for _ in range(random.randrange(20, 40)):
        x = r * x * (1 - x)
    return x


def lrelu(val):
    return val * 0.01 if val < 0 else val


def relu(val):
    return min(max(0, val), 100)


def tanh(val):
    return (2.0 / (1 + math.pow(math.e, -2 * val / 10.0))) - 1


class Dense:
    def __init__(self, input_size, output_size, activation):
        self.weights = np.zeros((input_size, output_size), dtype=np.single)
        self.bias = np.zeros(output_size, dtype=np.single)
        # self.weights = np.random.random((input_size, output_size))
        # self.bias = np.random.random(output_size)
        self.output = []
        self.activation = activation

    # TODO: optimize this ! (23% cpu) (17% without numpy)
    def call(self, _input):
        # numpy may be efficient for a large number of neuron
        # output = np.array([_input[i] * self.weights[i] for i in range(len(self.weights))]) # <- 4.5% on <listcomp>
        # output = np.multiply(_input[:,None], self.weights)
        # output += self.bias
        # output = np.array([self.activation(val) for val in output]) # <- 2.9% on <listcomp>, it's fine.
        # output = np.array([np.sum(output[:, i]) for i in range(len(self.weights[0]))]) # slowest (11% total)
        # output = np.sum(output[:,None]) # slowest (11% total)
        #        output = [_input[i] * self.weights[i] for i in range(len(self.weights))]
        #        output += self.bias
        #        output = [sum(output[:, i]) for i in range(len(self.weights[0]))]
        #        output = [self.activation(val) for val in output]
        output = np.sum(_input[:, None] * self.weights + self.bias, axis=0)    # it works
        output = np.fromiter((self.activation(val) for val in output), dtype=np.single)
        self.output = output
        return output

    def setRandomWeights(self, amt):
        self.weights = np.random.normal(0, amt, self.weights.shape)

    def setRandomBiases(self, amt):
        self.bias = np.random.normal(0, amt, self.bias.shape)


class AutoBrain:
    """
    https://www.heatonresearch.com/2017/06/01/hidden-layers.html
    I have a few rules of thumb that I use to choose hidden layers.
    There are many rule-of-thumb methods for determining an acceptable number of neurons to use in the hidden layers,
    such as the following:
    The number of hidden neurons should be between the size of the input layer and the size of the output layer.
    The number of hidden neurons should be 2/3 the size of the input layer, plus the size of the output layer.
    The number of hidden neurons should be less than twice the size of the input layer.

    KER approach : input -> input * 2, (optional input), input / 2, output
    """

    def __init__(self, auto):
        self.auto = auto
        self.num_input = 9
        self.input = []
        self.dense1 = Dense(self.num_input, 18, relu)
        self.dense2 = Dense(18, 9, lrelu)
        # self.dense3 = Dense(9, 4, relu)
        self.out = Dense(9, 2, tanh)
        self.randomize(self.auto.world.learning_rate)
        self.history = []

    def call(self, _input):
        self.input = _input
        _input = np.array(_input)
        output = self.dense1.call(_input)
        output = self.dense2.call(output)
        # output = self.dense3.call(output)
        output = self.out.call(output)
        return output

    def randomize(self, amt):
        # testing : only update some (1 = 50% chance, 2 = 66%, 3 = 75%, ...)
        if random.getrandbits(1):
            self.dense1.setRandomWeights(amt)
            self.dense1.setRandomBiases(amt)
        if random.getrandbits(1):
            self.dense2.setRandomWeights(amt)
            self.dense2.setRandomBiases(amt)
        # if random.getrandbits(1):
        #    self.dense3.setRandomWeights(amt)
        #    self.dense3.setRandomBiases(amt)
        if random.getrandbits(1):
            self.out.setRandomWeights(amt)
            self.out.setRandomBiases(amt)

    def mutate(self, parent, amt):
        self.randomize(amt)
        self.dense1.weights += parent.dense1.weights
        self.dense1.bias += parent.dense1.bias
        self.dense2.weights += parent.dense2.weights
        self.dense2.bias += parent.dense2.bias
        # self.dense3.weights += parent.dense3.weights
        # self.dense3.bias += parent.dense3.bias
        self.out.weights += parent.out.weights
        self.out.bias += parent.out.bias * amt
        for i in range(len(parent.auto.angles)):
            #old = (parent.auto.angles[i])   #KERU
            parent.auto.angles[i] += random.choice([-amt, 0, amt])
            #print("diff ", old - parent.auto.angles[i])   #KERU

    def draw(self, bounding_rect):
        """Draw the NN and joystick"""
        # return None
        # layers = [self.dense1, self.dense2, self.dense3, self.out]
        layers = [self.dense1, self.dense2, self.out]
        width = bounding_rect.size.x / (len(layers) + 1)
        last_layer = []
        height = bounding_rect.size.y / len(self.input)
        pos = Vector()
        pos.set(bounding_rect.pos)

        # KERU virtual joystick graph
        graph = []
        out_layer_i = len(layers) - 1
        graph.append(Circle(50, (0, 0), (200, 200, 200)))
        graph.append(Line((-50, 0), (50, 0), (0, 0, 0), 1))
        graph.append(Line((0, -50), (0, 50), (0, 0, 0), 1))
        graph.append(
            Circle(10, ((layers[out_layer_i].output[1]) * 50, (- layers[out_layer_i].output[0]) * 50), (50, 50, 50)))
        self.auto.world.viewer.draw(graph)
        self.history.append(
            Circle(2, ((layers[out_layer_i].output[1]) * 50, (- layers[out_layer_i].output[0]) * 50), (170, 0, 0)))
        self.auto.world.viewer.draw(self.history)

        # KERU add speed
        self.auto.world.viewer.draw([Line((-70, 50), (-70, 50 - self.input[7]), (0, 0, 200), 10)])
        # KERU add lat vel
        self.auto.world.viewer.draw([Line((-62, 70), (-60 + self.input[8], 70), (200, 200, 0), 10)])

        # KERU DRAW NN
        # return None

        for _input in self.input:
            activation = max(min((_input / 100), 1), 0)
            color = int(activation * 255)
            unit = Circle(6, pos, (color, color, color))
            unit.pos.add((0, height / 2.0))
            self.auto.world.viewer.draw([unit])
            pos.add((0, height))
            last_layer.append(unit)

        for i, layer in enumerate(layers):
            if len(layer.output) > 0:
                height = bounding_rect.size.y / len(layer.output)
                pos = Vector()
                pos.set(bounding_rect.pos)
                pos.add((width * (i + 1), 0))
                units = []
                conns = []

                for j, val in enumerate(layer.output):
                    if i < 2:
                        activation = max(min((val / 100.0), 1), 0)
                    else:
                        activation = max(min(((val + 1) / 2.0), 1), 0)

                    color = int(activation * 255)
                    unit = Circle(5, pos, (color, color, color))
                    unit.pos.add((0, height / 2.0))
                    pos.add((0, height))

                    for k, lunit in enumerate(last_layer):
                        activation = max(min(((abs(layer.weights[k][j])) / .2), 1), 0)
                        w = int(activation)  # KERU was 3 * activation + 1
                        # conn = Line(lunit.pos, unit.pos, (0, 0, 0), w)
                        conn = Line(lunit.pos, unit.pos, (activation * 128, activation, activation), w + 1)
                        conns.append(conn)

                    units.append(unit)

                self.auto.world.viewer.draw(conns)  # KERU draw NN
                self.auto.world.viewer.draw(last_layer)  # KERU drraw NN
                last_layer = units

        self.auto.world.viewer.draw(last_layer)


class Car(PhysicsEntity):
    def __init__(self, world):
        PhysicsEntity.__init__(self, world)
        self.body = Poly()
        self.body.setByRect(Rect())
        self.steering_angle = 0
        self.lat_vel = Vector()
        self.max_steering_angle = math.pi / 6
        # self.c_drag = .4257   # drag coef
        # self.c_rr = 12.8      # rolling resistance coef
        # self.c_tf = 12        # tyre friction coef
        self.c_drag = .4257  # drag coef
        self.c_rr = 12.8  # rolling resistance coef
        self.c_tf = 10  # tyre friction coef

        self.breakingForce = 300000  # KERU original is 100000
        self.engineForce = 1400000  # KERU : original is 350000
        self.accelerating = 0
        self.breaking = 0
        self.turning = 0

    def updatePos(self):
        self.body.pos = self.pos

    def updateFriction(self):
        """ apply drag, rolling resistance, and lateral friction"""
        if abs(self.vel.x) > .01 and abs(self.vel.y) > .01:
            """ apply the drag force """
            drag = Vector()
            drag.set(self.vel)
            d = self.c_drag * self.vel.getMag() * -1
            drag.mult((d, d))
            self.applyForce(drag)

            """ apply the rolling resistance force """
            rr = Vector()
            rr.set(self.vel)
            rr.mult((self.c_rr, self.c_rr))
            rr.mult((-1, -1))
            self.applyForce(rr)

        """ apply lateral friction"""
        line = -1 * self.c_tf * self.mass
        lateral = self.body.getMidPoint().getReciprocal()
        lat_vel = lateral.getProjection(self.vel)
        lat_vel.mult((line, line))
        self.lat_vel = lat_vel  # useful to add lat_vel as neuron input
        self.applyForce(lat_vel)

    def applyBreakingForce(self, amt=1):
        """ apply the breaking force """
        if not (self.vel.x == 0 and self.vel.y == 0) and (not amt == 0):
            br = self.body.getMidPoint()
            br.setMag(self.breakingForce * -amt)
            self.applyForce(br)

    def applyEngineForce(self, amt=1):
        """ apply the traction force """
        forward = self.body.getMidPoint()
        forward.setMag(self.engineForce * amt)
        self.applyForce(forward)

    def rotate(self):
        front = self.body.getMidPoint()
        end = Vector()
        end.set(front)
        end.mult((-1, -1))

        heading = Vector()
        heading.add(front)
        heading.sub(end)
        heading2 = Vector()
        heading2.set(heading)

        v = Vector()
        v.set(self.vel)
        v.mult((self.world.dt, self.world.dt))
        heading2.sub(v)
        v.rotate(self.steering_angle)
        heading2.add(v)
        d = -1 if heading2.y * heading.x < heading.y * heading2.x else 1
        self.body.rotate(heading.getAngleDiff(heading2) * d)
        heading2.setMag(self.vel.getMag())
        # self.vel = heading2

    def turn(self, direction):
        new_sa = direction * self.max_steering_angle
        diff = new_sa - self.steering_angle
        self.steering_angle += (diff * self.world.dt * 20)
        self.rotate()

    def input(self):
        for event in self.world.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.accelerating = 1
                if event.key == pygame.K_DOWN:
                    self.breaking = 1
                if event.key == pygame.K_RIGHT:
                    self.turning = 1
                if event.key == pygame.K_LEFT:
                    self.turning = -1

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    self.accelerating = 0
                if event.key == pygame.K_DOWN:
                    self.breaking = 0
                if event.key == pygame.K_RIGHT:
                    self.turning = 0
                if event.key == pygame.K_LEFT:
                    self.turning = 0

        if self.accelerating:
            self.applyEngineForce()

        if self.breaking:
            self.applyBreakingForce()

        if abs(self.turning):
            self.steering_angle = self.max_steering_angle * self.turning  # * self.world.dt
            # self.steering_angle = min(abs(self.steering_angle), self.max_steering_angle) * self.turning
            self.rotate()
        else:
            self.steering_angle = 0

    def colliding(self, line):
        lines = [Line(self.body.points[0], self.body.points[3]),
                 Line(self.body.points[1], self.body.points[2]),
                 Line(self.body.points[0], self.body.points[1])]

        for _line in lines:
            _line.shift((self.body.pos.x * -1, self.body.pos.y * -1))
            if _line.getLineIntercept(line) is not None:
                return 1
        return 0

    def update(self):
        self.updatePos()
        self.input()
        self.updateFriction()
        self.applyAcc()
        self.applyVel()

    def draw(self):

        end = self.body.getMidPoint()
        end.add(self.body.pos)
        start = Vector()
        start.set(self.body.pos)
        line = Line(start, end)
        self.world.viewer.draw([self.body, line])



class RaceCar(Car):
    def __init__(self, world):
        Car.__init__(self, world)
        self.current_track = 0
        # self.last_gateTime = timeit.default_timer()
        self.stop = 0

    def start(self):
        ct = self.world.track.tracks[self.current_track]
        self.pos.set(ct.getCenter())

        orientation = Vector()
        orientation.set(ct.next_track.gate.end)
        orientation.add(ct.next_track.gate.start)
        orientation.div((2, 2))
        self.world.viewer.draw([Circle(5, orientation)])
        orientation.sub(self.pos)

        # TODO : find a bug here
        for i in range(100):
            direction = self.body.getMidPoint()
            a = orientation.getAngleDiff(direction)
            a *= -1 if orientation.y / (direction.y * orientation.x) > direction.x else 1
            self.body.rotate(a)
            line_direction = self.body.getMidPoint()
            if line_direction.x == direction.x and line_direction.y == direction.y:
                break

    def getCurrentGate(self):
        return self.world.track.tracks[self.current_track]

    def updateCurrentTrack(self):
        ct = self.world.track.tracks[self.current_track]

        if self.colliding(ct.next_track.gate):
            self.nextGate()

    def nextGate(self):
        self.current_track = (self.current_track + 1) % len(self.world.track.tracks)

    def updateCol(self):
        ct = self.world.track.tracks[self.current_track]
        lt = self.world.track.tracks[(self.current_track - 1) % len(self.world.track.tracks)]

        for line in [ct.track_inner, ct.track_outer, lt.track_inner, lt.track_outer, lt.gate]:
            if self.colliding(line):
                self.crash()

    def crash(self):
        self.stop = 1

    def update(self):
        if not self.stop:
            # self.start()
            self.updatePos()
            self.input()
            self.updateFriction()
            self.applyAcc()
            self.applyVel()
            self.updateCurrentTrack()
            self.updateCol()


class Auto(RaceCar):
    next_id = 0

    def __init__(self, world, parent=None):
        RaceCar.__init__(self, world)
        self.start_time = pygame.time.get_ticks()
        self.current_track = 0
        self.top = 0
        if not parent:
            self.angles = [-90, -45, -20, 0, 20, 45, 90]
            #for _ in range(7):
            #    self.angles.append(random.randint(-90, 90))
        else:
            self.angles = parent.angles
        # self.angles = [] #[-90, -45, -20, 0, 20, 45, 90]

        self.brain = AutoBrain(self)
        self.engine_amt = 0  # 0 - 1
        self.break_amt = 0  # 0 - 1
        self.turn_amt = 0  # -1 - 1
        self.fitness = 0
        self.inputs = []
        self.gen = world.generation
        self.parent = parent
        self.id = Auto.next_id
        Auto.next_id += 1


    def getName(self):
        return "Auto_{}".format(self.id) if self.parent is None else "{}_{}".format(self.parent.name, self.id)

    def start(self):
        self.fitness = 0
        self.current_track = 0
        self.stop = 0
        self.vel.set((0, 0))
        self.acc.set((0, 0))
        RaceCar.start(self)
        self.getCurrentGate().activate()
        self.stop = 0
        self.start_time = pygame.time.get_ticks()

    def nextGate(self):
        if self.top:
            self.getCurrentGate().deactivate()
        RaceCar.nextGate(self)
        if self.top:
            self.getCurrentGate().activate()
        self.fitness += 1

    def getInputs(self) -> []:
        max_dis = 200  # KERU
        angles = self.angles
        # for i, a in enumerate(angles):  # KERU add some noise
        #    a += random.random() * 2 - 0.5
        #    angles[i] = a
        # print(angles)
        self.inputs = []
        inputs = []

        for angle in angles:
            start = Vector()
            start.set(self.pos)
            end = self.body.getMidPoint(0, 1)
            end.rotate(angle, degree=True)
            end.setMag(max_dis)
            end.add(start)
            ray = Line(start, end)
            col = None
            i = 0

            cols = []  # TODO : not sure if here or below
            while i < len(self.world.track.tracks) and col is None:
                min_dis = None
                col = None
                index = math.ceil(i / 2.0) * (((i % 2) * 2) - 1)
                track = self.world.track.tracks[(index + self.current_track) % len(self.world.track.tracks)]
                walls = [track.track_inner, track.track_outer]

                for wall in walls:
                    c = ray.getLineIntercept(wall)
                    if c is not None:
                        cols.append(c)

                for c in cols:
                    dis = start.getDis(c)
                    if min_dis is None or dis < min_dis:
                        min_dis = dis
                        col = c

                i += 1

            #            if pygame.time.get_ticks() - self.start_time > 2000:
            #                if not cols:  # same as if len(cols) == 0
            #                    self.stop = 1  # KERU collision fix

            if col is None:
                col = end

            # Show the ray and circle of the "lidar" input sensor
            if self.top:
                self.inputs.append(Circle(3, col, (0, 0, 120)))
                self.inputs.append(Line(start, col, (0, 0, 120), width=1))

            dis = start.getDis(col)
            inputs.append(dis)

        return inputs

    def getOutput(self, _input):
        output = self.brain.call(_input)
        self.engine_amt = max(0, output[0])
        self.break_amt = min(0, output[0])
        self.turn_amt = output[1]

    def act(self):
        _input = self.getInputs()
        _input.append(self.vel.getMag() / 20)  # add speed as input
        _input.append(self.lat_vel.getMag() / 15000)  # add lateral velocity as input
        self.getOutput(_input)
        self.applyBreakingForce(self.break_amt)
        self.applyEngineForce(self.engine_amt)
        self.turn(self.turn_amt)

    def update(self):
        if not self.stop:
            self.act()
            self.updateFriction()
            self.applyAcc()
            self.applyVel()
            self.updatePos()
            self.updateCurrentTrack()
            self.updateCol()

        c = (51, 51, 51)
        if self.gen != self.world.generation - 1:
            c = (200, 180, 140)
        elif self.top:
            c = (20, 255, 230)

        self.body.color = c

    def makeChild(self, lr=None):
        if lr is None:
            lr = self.world.learning_rate
        child = Auto(self.world, self)
        child.brain.mutate(self.brain, lr)
        return child
