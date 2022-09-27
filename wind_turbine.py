#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Created By  : Paul Aubin
# Created Date: 2022/09/26
# ---------------------------------------------------------------------------
""" Environment to simulate a wind turbine """
# ---------------------------------------------------------------------------

import numpy as np
import matplotlib.pyplot as plt
from math_utils import wrap_to_m180_p180

class Wind_turbine:
	def __init__(self):
		pass

	def rotate(self, direction):
		if direction == -1 :
			# rotate trigo
			self.wind_rel_heading_hist[-1] -= self.angle_increment
			self.control_on = True
		if direction == +1 :
			# rotate clockwise
			self.wind_rel_heading_hist[-1] += self.angle_increment
			self.control_on = True
		if direction == 0 :
			# stays in place
			self.control_on = False
		if direction != -1 and direction != +1 and direction != 0 :
			print('wind turbine command ', direction, ' not valid')
			self.control_on = False

# Model of the wind
class Wind:
	model = 'OU' 					# model used for wind simulation
	__c_speed_factor = 0.2 			# variable used in the OU model
	__speed_noise = 0.1 			# variable used in the OU model
	__c_heading_factor = 0.005 		# variable used in the OU model
	__heading_noise = 0.3 			# variable used in the OU model
	__speed_target = 0.0 			# m/s, represents the average wind speed on some minutes
	__heading_target = 0.0 			# deg, represents the average wind angle on some minutes
	__diurnal_period = 24*3600 		# s, represents the period of the diurnal cycle
	__diurnal_factor = 0.2 			# represents the wind speed elliptical coefficient on a diurnal cycle
	__time = 0 						# s, represent the elapsed time in s due to the cumulative steps

	def __init__(self, initial_speed=None, initial_heading=None, step_duration=None, time_of_the_day=None, model_type='OU'):
		''' 
		Inputs :
			heading 		- [deg] The wind angle wrt Northin degree
			speed 			- [m/s] A negative speed would result in a 180° shift in heading
			step_duration 	- [s] 	The duration of a time step. It should be higher or equal to 1s
			time_of_the_day - [s]	For instance 7H30AM is 7*3600 + 30*60. By default it is set to midnight
			model_type		- [] 	The model used to simulate the wind, the 'OU'
									model is the one selected by default and corresponds to the 
									Ornstein-Uhlenbeck model
		'''
		self._speed = 0 if initial_speed is None else initial_speed
		self._heading = 0 if initial_heading is None else initial_heading
		self.__step_duration = self.__dt if step_duration is None else step_duration
		self.__time = 0 if time_of_the_day is None else time_of_the_day
		self.model_type = model_type

		# Initialise hidden variables. The heading and speed target corresponds to the
		# average on which the OU process must tend. They vary slowly whereas the OU
		# process accounts for fast variations such as gusts
		self.__speed_init = self._speed
		self.__heading_init = self._heading

	def step(self, model='OU'):
		'''
		step_duration must be an int
		'''
		# Increment time and compute long term speed and heading duration
		self.__time += self.__step_duration
		self.__diurnal_cycle()

		# Compute short term variations
		if self.model == 'OU':
			mean_sp = self._speed
			mean_hd = self._heading
			steps = 1
			for i in range(int(np.ceil(self.__step_duration))):
				# Compute fast chaning wind at 1/dt frequency, typically 1Hz
				self.__ou()
				steps += 1
				mean_sp += (self._speed - mean_sp)/steps
				mean_hd += (self._heading - mean_hd)/steps
				if i % self.__step_duration == 1:
					# Flush new value
					self._speed = mean_sp
					self._heading = mean_hd
					# Reset incremental mean
					mean_sp = self._speed
					mean_hd = self._heading
					steps = 1
		else:
			print('Wind model not found in class ', str(self.__class__))

	def __ou(self):
		'''
		This is the Ornstein-Uhlenbeck process, a stationary Gauss-Markov model,
		a math definition is available at page 7 here : https://www.merl.com/publications/docs/TR2022-102.pdf
		'''
		c_speed = self.__c_speed_factor * self.__speed_target
		# The random distribution variance is chosen such that wind gust can reach 40% of the average wind. Support for random walk and normal distribution
		# is available here : https://en.wikipedia.org/wiki/Random_walk#:~:text=A%20random%20walk%20having%20a,walk%20as%20an%20underlying%20assumption
		self._speed = c_speed + (1 - self.__c_speed_factor) * self._speed + np.random.normal(0.0, self.__speed_noise * np.abs(self.__speed_target))

		c_heading = self.__c_heading_factor * self.__heading_target
		self._heading = c_heading + (1 - self.__c_heading_factor) * self._heading + np.random.normal(0.0, self.__heading_noise)

	def __diurnal_cycle(self):
		'''
		The diurnal cycles is modelised as an elliptic day-night shift of the wind : https://en.wikipedia.org/wiki/Ellipse 
		'''
		u = np.tan((2 * np.pi * self.__time / self.__diurnal_period) / 2)
		x = (1 - u**2)/(1 + u**2)
		y = self.__diurnal_factor * (2*u) / (1 + u**2)
		self.__speed_target = np.sqrt(x**2 + y**2) * self.__speed_init
		self.__heading_target = np.mod(np.arctan2(y, x) * 180/np.pi, 360) + self.__heading_init
		

	@property
	def heading(self):
		if self._speed < 0:
			return np.mod(self._heading + 180, 360)
		else:
			return np.mod(self._heading, 360)
	@property
	def speed(self):
		return np.abs(self._speed)
	
	def __str__(self):
		return str(self.__class__) + ": " + str(self.__dict__)
		

w1 = Wind(10, 0, 1, 0,  'OU')
w2 = Wind(10, 0, 10, 6*3600, 'OU')

time1 = np.linspace(0, 24*3600, 24*3601)
w1_sp_log = np.zeros((np.size(time1), 1))
w1_h_log = np.zeros((np.size(time1), 1))
for t in range(len(time1)) :
	w1_sp_log[t] = w1.speed
	w1_h_log[t] = w1.heading
	w1.step()

time2 = np.linspace(0, 24*3600, 24*361)
w2_sp_log = np.zeros((np.size(time2), 1))
w2_h_log = np.zeros((np.size(time2), 1))
for t in range(len(time2)) :
	w2_sp_log[t] = w2.speed
	w2_h_log[t] = w2.heading
	w2.step()

print('mean speed 1= ', np.mean(w1_sp_log))
print('std speed 1= ', np.std(w1_sp_log))
print('mean heading 1= ', np.mean(w1_h_log))
print('std heading 1= ', np.std(w1_h_log))

print('mean speed 2= ', np.mean(w2_sp_log))
print('std speed 2= ', np.std(w2_sp_log))
print('mean heading 2= ', np.mean(w2_h_log))
print('std heading 2= ', np.std(w2_h_log))

fig, axs = plt.subplots(2, sharex=True)
axs[0].plot(time1, w1_sp_log, label='step = 1')
axs[0].plot(time2, w2_sp_log, label='step = 10')
axs[0].set(xlabel = 'Time (s)', ylabel='Speed (m/s)')
axs[0].grid()
axs[1].plot(time1, w1_h_log, label='step = 1')
axs[1].plot(time2, w2_h_log, label='step = 10')
axs[1].set(xlabel = 'Time (s)', ylabel='Heading (°)')
axs[1].grid()
fig.set_size_inches(14, 8)
plt.show()